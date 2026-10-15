import os
import pytest
from ldap3 import Server, Connection, SIMPLE
from ldap3.core.exceptions import LDAPBindError

HOST = os.getenv('LDAP_HOST', '127.0.0.1')
PORT = int(os.getenv('LDAP_PORT', '1389'))
BASE = 'dc=example,dc=org'
# 镜像默认 ACL 只授予匿名 auth 权限：普通用户可 Bind 不可搜索，
# 搜索需用目录管理员凭证（公开测试凭据，与 .env.example 一致，可用环境变量覆盖）。
ADMIN_DN = os.getenv('LDAP_BIND_DN', f'cn=admin,{BASE}')
ADMIN_PASSWORD = os.getenv('LDAP_BIND_PASSWORD', 'admin123')


def connect(uid: str, password: str) -> Connection:
    return Connection(
        Server(HOST, port=PORT, use_ssl=False),
        user=f'uid={uid},ou=people,{BASE}',
        password=password,
        authentication=SIMPLE,
        auto_bind=True,
    )


def connect_admin() -> Connection:
    return Connection(
        Server(HOST, port=PORT, use_ssl=False),
        user=ADMIN_DN,
        password=ADMIN_PASSWORD,
        authentication=SIMPLE,
        auto_bind=True,
    )


@pytest.mark.parametrize('uid', [
    'admin01', 'admin02', 'dev01', 'dev02', 'dev03',
    'test01', 'test02', 'test03', 'user01', 'user02'
])
def test_all_users_can_bind(uid):
    with connect(uid, 'Test123456') as conn:
        assert conn.bound


def test_wrong_password_fails():
    with pytest.raises(LDAPBindError):
        connect('dev01', 'WRONG_PASSWORD')


def test_unknown_user_fails():
    with pytest.raises(LDAPBindError):
        connect('not-exists', 'Test123456')


def test_search_user_by_uid_returns_unique_dn():
    with connect_admin() as conn:
        assert conn.search(
            f'ou=people,{BASE}',
            '(uid=dev01)',
            attributes=['uid'],
        )
        assert len(conn.entries) == 1
        assert conn.entries[0].entry_dn == f'uid=dev01,ou=people,{BASE}'


def test_group_membership():
    with connect_admin() as conn:
        assert conn.search(
            f'ou=groups,{BASE}',
            f'(member=uid=dev01,ou=people,{BASE})',
            attributes=['cn'],
        )
        assert any('developers' in entry.cn.values for entry in conn.entries)


def test_developers_has_exactly_three_members():
    with connect_admin() as conn:
        assert conn.search(
            f'ou=groups,{BASE}',
            '(cn=developers)',
            attributes=['member'],
        )
        members = sorted(conn.entries[0].member.values)
        assert members == sorted([
            f'uid=dev01,ou=people,{BASE}',
            f'uid=dev02,ou=people,{BASE}',
            f'uid=dev03,ou=people,{BASE}',
        ])


def test_admins_and_testers_memberships():
    with connect_admin() as conn:
        assert conn.search(
            f'ou=groups,{BASE}',
            '(|(cn=admins)(cn=testers))',
            attributes=['cn', 'member'],
        )
        by_cn = {entry.cn.value: entry for entry in conn.entries}
        assert set(by_cn) == {'admins', 'testers'}
        assert sorted(by_cn['admins'].member.values) == sorted([
            f'uid=admin01,ou=people,{BASE}',
            f'uid=admin02,ou=people,{BASE}',
        ])
        assert sorted(by_cn['testers'].member.values) == sorted([
            f'uid=test01,ou=people,{BASE}',
            f'uid=test02,ou=people,{BASE}',
            f'uid=test03,ou=people,{BASE}',
        ])


@pytest.mark.parametrize('uid', ['user01', 'user02'])
def test_user_without_group(uid):
    with connect_admin() as conn:
        conn.search(
            f'ou=groups,{BASE}',
            f'(member=uid={uid},ou=people,{BASE})',
            attributes=['cn'],
        )
        assert len(conn.entries) == 0
