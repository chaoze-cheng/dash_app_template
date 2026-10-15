#!/usr/bin/env bash
set -euo pipefail
CONTAINER=ldap-mock-server
BASE='dc=example,dc=org'
PASS='Test123456'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
[ -f "$SCRIPT_DIR/../.env" ] && { set -a; source "$SCRIPT_DIR/../.env"; set +a; }
ADMIN_DN="cn=admin,${BASE}"
ADMIN_PASS="${LDAP_ADMIN_PASSWORD:?Create .env from .env.example (need LDAP_ADMIN_PASSWORD)}"

# 等待 LDAP 响应，最多 30 次尝试；避免 depends_on != ready 的竞态。
ready=0
for _ in $(seq 1 30); do
  if docker exec "$CONTAINER" ldapwhoami -x -H ldap://localhost:389 \
       -D "uid=dev01,ou=people,$BASE" -w "$PASS" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
[ "$ready" -eq 1 ] || { echo 'LDAP not ready or seed missing' >&2; exit 1; }

for user in admin01 admin02 dev01 dev02 dev03 test01 test02 test03 user01 user02; do
  docker exec "$CONTAINER" ldapwhoami -x -H ldap://localhost:389 \
    -D "uid=$user,ou=people,$BASE" -w "$PASS" >/dev/null
  echo "PASS bind: $user"
done

# 错误密码必须拒绝认证。
if docker exec "$CONTAINER" ldapwhoami -x -H ldap://localhost:389 \
     -D "uid=dev01,ou=people,$BASE" -w WRONG_PASSWORD >/dev/null 2>&1; then
  echo 'FAIL: invalid password accepted' >&2
  exit 1
fi
echo 'PASS reject: wrong password'

# 不存在账号必须拒绝认证。
if docker exec "$CONTAINER" ldapwhoami -x -H ldap://localhost:389 \
     -D "uid=not-exists,ou=people,$BASE" -w "$PASS" >/dev/null 2>&1; then
  echo 'FAIL: unknown user accepted' >&2
  exit 1
fi
echo 'PASS reject: unknown user'

# 镜像默认 ACL 仅授予匿名 auth 权限，搜索需用目录管理员凭证（取自 .env，不硬编码）。
search() { # search <base> <filter> [attrs...]
  docker exec "$CONTAINER" ldapsearch -x -LLL -H ldap://localhost:389 \
    -D "$ADMIN_DN" -w "$ADMIN_PASS" -b "$1" "$2" "${@:3}"
}

# 计数断言：恰好 10 个用户。
user_count=$(search "ou=people,$BASE" '(objectClass=inetOrgPerson)' uid | grep -c '^uid: ')
[ "$user_count" -eq 10 ] || { echo "FAIL: expected 10 users, got $user_count" >&2; exit 1; }
echo 'PASS count: 10 users'

# 计数断言：恰好 3 个组。
group_count=$(search "ou=groups,$BASE" '(objectClass=groupOfNames)' cn | grep -c '^cn: ')
[ "$group_count" -eq 3 ] || { echo "FAIL: expected 3 groups, got $group_count" >&2; exit 1; }
echo 'PASS count: 3 groups'

# 按 uid 搜索用户，返回唯一 DN。（不用 grep -q：pipefail 下提前退出会触发 SIGPIPE）
search "ou=people,$BASE" '(uid=dev01)' dn | grep -cx 'dn: uid=dev01,ou=people,dc=example,dc=org' >/dev/null
echo 'PASS search: dev01 unique DN'

# developers 组成员必须是 dev01/dev02/dev03。
members=$(search "ou=groups,$BASE" '(cn=developers)' member | grep '^member: ' | sort)
expected=$(printf 'member: uid=dev01,ou=people,dc=example,dc=org\nmember: uid=dev02,ou=people,dc=example,dc=org\nmember: uid=dev03,ou=people,dc=example,dc=org\n' | sort)
[ "$members" = "$expected" ] || { echo "FAIL: developers membership mismatch" >&2; exit 1; }
echo 'PASS group: developers members'

# admins / testers 组成员抽查。
search "ou=groups,$BASE" '(cn=admins)' member | grep 'uid=admin02,ou=people' >/dev/null
search "ou=groups,$BASE" '(cn=testers)' member | grep 'uid=test03,ou=people' >/dev/null
echo 'PASS group: admins/testers members'

# 无组用户不得出现在任何组里。
grouped=$(search "ou=groups,$BASE" '(|(member=uid=user01,ou=people,dc=example,dc=org)(member=uid=user02,ou=people,dc=example,dc=org))' dn | grep -c '^dn: ' || true)
[ "$grouped" -eq 0 ] || { echo "FAIL: user01/user02 unexpectedly in $grouped group(s)" >&2; exit 1; }
echo 'PASS nogroup: user01/user02'

echo 'PASS: smoke tests'
