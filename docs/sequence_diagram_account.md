# 계정 관리

## **컨셉**

- 계정을 생성/삭제 할 수 있다.
- 프로젝트 내 계정을 포함/제외 할 수 있다.
- ID / Password 를 기반으로 인증을 제공한다.
- 도메인과 프로젝트는 미리 생성하여 제공된 것을 사용한다.

## **프로젝트**

### 프로젝트 목록을 조회할 수 있다.

- 검색 조건
    - 프로젝트 ID (equal, in, not)
    - 프로젝트 이름 (equal, like)
- 정렬 조건
    - 이름
    - 생성일
- 응답에는 반드시 다음 값이 필요하다.
    - 프로젝트 ID
    - 프로젝트 이름
    - 프로젝트가 속한 도메인 정보
        - 도메인 ID
        - 도메인 이름
    - 프로젝트에 속한 계정 목록
        - 계정 ID
        - 계정 로그인 ID
        - 계정 이름
    - 생성일
    - 수정일
    - 삭제일

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant DB
    Client ->>+ Server: API request
    Server -)+ DB: fetch
    DB --)- Server: query result
    Server -->>- Client: response

```

### 프로젝트를 단일 조회할 수 있다.

- 응답에는 반드시 다음 값이 필요하다.
    - 프로젝트 ID
    - 프로젝트 이름
    - 프로젝트가 속한 도메인 정보
        - 도메인 ID
        - 도메인 이름
    - 프로젝트에 속한 계정 목록
        - 계정 ID
        - 계정 로그인 ID
        - 계정 이름
    - 생성일
    - 수정일
    - 삭제일

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant DB
    Client ->>+ Server: API request
    Server -)+ DB: fetch
    DB --)- Server: query result

    opt not found
        Server -->> Client: 404 Not Found
    end
    Server -->>- Client: 200 OK
```

### 프로젝트를 변경할 수 있다.

- 다음 조건을 만족해야 한다.
    - 다른 프로젝트와 이름을 중복할 수 없다.

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant DB
    participant OS as OpenStack
    Client ->>+ Server: PUT /projects/{project_id}
    Server -)+ DB: 프로젝트 조회
    DB --) Server: response
    opt 프로젝트 not found
        Server -->> Client: 404 error response
    end
    Server -) DB: 프로젝트 변경 권한 확인
    DB --) Server: response
    opt 프로젝트 변경 권한 없음
        Server -->> Client: 403 error response
    end
    Server -) DB: 중복 이름 확인
    DB --) Server: response
    opt 이름 중복
        Server -->> Client: 409 error response
    end

    Server -) DB: update
    DB --) Server: response
    Server -)+ OS: (Keystone) PATCH /v3/projects/{project_id}
    OS --)- Server: response
alt fail
Note over Server, OS: 보상트랜잭션 발행
Server-)DB: rollback
DB--)Server: 
            Server-)+OS: (keystone) PATCH /v3/projects/{project_id}
OS--)-Server:
Server-->>Client: error response
else success
Server-)DB: commit
DB--)-Server:
Server-->>-Client: response
end
```

### 프로젝트에 계정을 소속시킬 수 있다.

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant DB
    participant OS as OpenStack
    Client ->>+ Server: POST projects/{project_id}/users/{user_id}
    Server -)+ DB: 프로젝트 조회
    DB --) Server: response
    opt 프로젝트 not found
        Server -->> Client: 404 error response
    end
    Server -) DB: 유저 조회
    DB --) Server: response
    opt 유저가 not found
        Server -->> Client: 404 error response
    end
    Server -) DB: 프로젝트 변경 권한 확인
    DB --) Server: response
    opt 프로젝트 변경 권한 없음
        Server -->> Client: 403 error response
    end
    Server -) DB: 프로젝트에 소속된 유저인지 확인
    DB --) Server: response
    opt 이미 소속 되어있음
        Server -->> Client: 409 error response
    end

    Server -) DB: 유저, 프로젝트 관계 테이블에 row 추가
    DB --) Server: response
    Server -)+ OS: (keystone) PUT /v3/projects/{project_id}/users/{user_id}/roles/{role_id}
    OS --)- Server: response
alt fail
Note over Server, OS: OpenStack 보상트랜잭션 발행
Server-)DB: rollback
DB--)Server: 
          Server-)+OS: (keystone) DELETE /v3/projects/{project_id}/users/{user_id}/roles/{role_id}
OS--)-Server:
Server-->>Client: error response
else success
Server-)DB: commit
DB--)-Server:
Server-->>-Client: response
end
```

### 프로젝트에서 계정을 제외시킬 수 있다.

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant DB
    participant OS as OpenStack
    Client ->>+ Server: DELETE projects/{project_id}/users/{user_id}
    Server -)+ DB: 프로젝트 조회
    DB --) Server: response
    opt 프로젝트 not found
        Server -->> Client: 404 error response
    end
    Server -) DB: 유저 조회
    DB --) Server: response
    opt 유저가 not found
        Server -->> Client: 404 error response
    end
    Server -) DB: 프로젝트 변경 권한 확인
    DB --) Server: response
    opt 프로젝트 변경 권한 없음
        Server -->> Client: 403 error response
    end
    Server -) DB: 프로젝트에 소속된 유저인지 확인
    DB --) Server: response
    opt 소속되어 있지 않음
        Server -->> Client: 409 error response
    end
    Server -) DB: 유저, 프로젝트 관계 테이블에 row 삭제
    DB --) Server: response
    Server -)+ OS: (Keystone) DELETE /v3/projects/{project_id}/users/{user_id}/roles/{role_id}
    OS --)- Server: response
alt fail
Note over Server, OS: OpenStack 보상트랜잭션 발행
Server-)DB: rollback
DB--)Server: 
          Server-)+OS: (Keystone) POST /v3/projects/{project_id}/users/{user_id}/roles/{role_id}
OS--)-Server:
Server-->>Client: error response
else success
Server-)DB: commit
DB--)-Server:
Server-->>-Client: response
end
```

## **계정**

### 계정 목록을 조회할 수 있다.

- 검색 조건
    - 계정 ID
    - 로그인 ID
    - 계정 이름
- 정렬 조건
    - 가입일
    - 로그인 ID
    - 계정 이름
- 응답에는 반드시 다음 값이 필요하다.
    - 계정 ID
    - 로그인 ID
    - 계정 이름
    - 계정이 속한 프로젝트 목록
        - 프로젝트 ID
        - 프로젝트 이름
    - 계정이 속한 도메인 정보
        - 도메인 ID
        - 도메인 이름
    - 생성일
    - 수정일
    - 삭제일

```mermaid
sequenceDiagram
    participant c as Client
    participant s as Server
    participant db as DB
    c ->>+ s: GET /users
    s -)+ db: find users with deleted
    db --)- s: response
    s -->>- c: response
```

### 계정을 단일 조회할 수 있다.

- 응답에는 반드시 다음 값이 필요하다.
    - 계정 ID
    - 로그인 ID
    - 계정 이름
    - 계정이 속한 프로젝트 목록
        - 프로젝트 ID
        - 프로젝트 이름
    - 계정이 속한 도메인 정보
        - 도메인 ID
        - 도메인 이름
    - 생성일
    - 수정일
    - 삭제일

```mermaid
sequenceDiagram
    participant c as Client
    participant s as Server
    participant db as DB
    c ->>+ s: GET /users/{user_id}
    s -)+ db: find user (with deleted)
    db --)- s: response
    opt user not found
        s -->> c: 404 error response
    end
    s -->>- c: response
```

### 회원 가입을 할 수 있다.

- 로그인 ID 는 전체 계정에서 중복할 수 없다.

```mermaid
sequenceDiagram
    participant c as Client
    participant s as Server
    participant db as DB
    participant os as OpenStack
    c ->>+ s: POST /users
    s -)+ db: `account_id` 사용 여부 확인
    db --) s: response
    opt 만약 사용중인 `account_id`라면
        s -->> c: 409 error response
    end

    s -)+ os: [Keystone] 관리자 권한으로 keystone token 발행 (POST /v3/auth/tokens)
    os --)- s: response
    s -)+ os: [Keystone] 유저 생성 (POST /v3/users)
    os --)- s: response
    s -) db: create user
    db --) s: response

alt fail
Note over s, os: 보상 트랜잭션 발행
s-)db: rollback
db--)s: 
      s-)+os: [Keystone] 생성된 유저 삭제 DELETE /v3/users/{user_id}
os--)-s:
s-->>c: error response
else success
s-)db: commit
db--)-s:
s-->>-c: response
end
```

### 유저 정보를 변경할 수 있다.

```mermaid
sequenceDiagram
    participant c as Client
    participant s as Server
    participant db as DB
    c ->>+ s: PUT /users/{user_id}/info

    opt 요청한 유저 != 변경할 유저
        s -->> c: 403 error response
    end

    s -)+ db: 변경할 유저 조회
    db --) s: response
    opt user not found
        s -->> c: 404 error response
    end

    s -) db: update user info
    db --)- s: response
    s -->>- c: response
```

### 회원 탈퇴가 가능해야 한다.

- 마지막 남은 계정은 삭제할 수 없다.

```mermaid
sequenceDiagram
    participant c as Client
    participant s as Server
    participant db as DB
    participant os as OpenStack
    c ->>+ s: DELETE /users/me
    s -)+ db: 삭제할 유저 조회
    db --) s: response
    opt user not found
        s -->> c: 404 error response
    end

    s -) db: 삭제되지 않은 유저 수 조회
    db --) s: response

    opt 삭제되지 않은 유저 수 <= 1
        s -->> c: 400 error response
    end

    s -)+ os: [Keystone] DELETE /v3/users/{user_id}
    os --)- s: 204 response
    s -) db: 유저가 소속된 모든 프로젝트에서 유저를 제거
    db --) s: response
    s -) db: 유저 삭제
    db --)- s: response
    s -->>- c: 204 response
```

## **인증**

### id/password 로그인을 제공한다.

- 자신이 속한 프로젝트에만 로그인할 수 있다.
- 프로젝트 ID 를 제공받아 명시적으로 로그인 프로젝트를 지정할 수 있다.
- 프로젝트 ID 가 없으면 자동으로 프로젝트 하나를 지정해 로그인한다.
- 어떠한 프로젝트에도 속하지 않은 계정은 로그인 할 수 없다.

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant DB
    participant OS as OpenStack
    Client ->>+ Server: API request
    Server -)+ DB: account_id로 유저 조회
    DB --)- Server: response
    Server ->> Server: password 검증

    alt project_id가 주어지지 않은 경우
        Server -)+ DB: 소속된 프로젝트 중 하나 조회 및 선택
        DB --)- Server: response
    else project_id가 주어진 경우
        Server -)+ DB: 주어진 id에 해당하는 프로젝트 조회 및 선택
        DB --)- Server: response
    end

    Server -)+ OS: [Keystone] POST /v3/auth/tokens (scoped)
    OS --)- Server: response
    Server ->> Server: access token 발행
    Server -->>- Client: response
```

