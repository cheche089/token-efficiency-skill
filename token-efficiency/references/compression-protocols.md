# Compression Protocols

Detailed formats and procedures for compressing histories, files, and contexts.

---

## Conversation Block Compression

### When to compress
A conversation block is ready for compression when:
- You understand what was discussed
- A decision was reached
- The topic is no longer actively being discussed
- The content is more than 2 turns old

### Compression templates

**Task Completion**
```
[TASK] {verb in past tense} {object}
# Examples:
[TASK] Set up database schema for user profiles
[TASK] Added pagination to user list endpoint
[TASK] Debug rate limiter not applying to POST requests
```

**Decision**
```
[DECISION] {topic} → {outcome} (alt: {alt considered}) (reason: {justification})
# Examples:
[DECISION] Auth method → JWT RS256 (alt: OAuth2) (reason: simpler for internal API)
[DECISION] Pagination style → page/page_size (alt: cursor) (reason: simpler for MVP)
[DECISION] DB engine → PostgreSQL (alt: SQLite) (reason: concurrent write needs)
```

**File Analysis**
```
[FILE] {path} [{hash[:8]}] → {one-line summary} | {key classes/defs}
# Examples:
[FILE] src/config.py [a1b2c3d4] → App config, DB URL from env | Config class
[FILE] src/auth/middleware.py [e5f6g7h8] → JWT validation middleware | verify_token(), AuthMiddleware class
[FILE] tests/test_auth.py [f9g8h7i6] → Auth test suite, 3 test cases | test_login, test_token_expiry, test_invalid_token
```

**Progress**
```
[PROGRESS] {task} | {done|pending|blocked|in_progress} | {detail/blocker}
# Examples:
[PROGRESS] DB schema design | done | 3 tables: users, posts, comments
[PROGRESS] API route implementation | in_progress | GET /users done, POST /users working
[PROGRESS] Test setup | blocked | waiting for mock DB config
```

### Aggregated compression (for entire turn)
At the end of each turn, produce a single compressed block:
```
=== TURN {N} COMPRESSED ===
[TASK] Auth module audit
[DECISION] Use JWT RS256 (reason: internal API simplicity)
[FILE] src/auth/config.py: Config reads JWT_SECRET from env
[FILE] src/auth/middleware.py: verify_token() validates RS256 sig
[PROGRESS] Auth audit | done | findings: 1 minor issue (missing fallback key)

[BUDGET:files=2/10 lines=340/5000 bytes=12KB/50KB]
[CONTEXT] Ready for next: implement audit recommendations
=== END TURN {N} ===
```

---

## File Content Compression

When a file is too large to cache fully (>100 KB or >1000 lines), compress on read:

### Compression levels

**Level 1: Header-only** (< 20 tokens)
For well-known libraries, generated code, or when you only need the file's purpose.
```
# src/utils/helpers.py: Utility functions for string manipulation.
# Headers: from datetime import datetime, import re
# Read Level 1 — skipping body.
```

**Level 2: Structure-only** (~100 tokens)
For medium files where you need to know what's available but not the implementation.
```
# src/services/user_service.py
# Classes: UserService (methods: create_user, get_user, update_user, delete_user)
# Functions: validate_email, hash_password, send_welcome_email
# Dependencies: User model, mail service, hash lib
```

**Level 3: Key logic** (~400 tokens)
For files where you need to understand specific functions or logic.
```
# src/auth/middleware.py
# verify_token():
#   1. Extract token from Authorization header
#   2. Verify RS256 signature using public key from Vault
#   3. Check expiry from token payload
#   4. Return user_id if valid, raise 401 if invalid
# AuthMiddleware class:
#   __init__: takes excluded_paths list
#   __call__: runs verify_token on all paths except excluded_paths
```

**Level 4: Full read** (file size in tokens)
For files you need to modify or deeply understand.

### Selection rule
Hesitate before Level 4. If you're reading for understanding, not modification, Levels 1-3 suffice.

---

## Context Compression Cycle

```
Start of turn
├─ [PRUNE] Drop stale blocks
├─ Check [CONTEXT] memory
├─ Read compressed summaries of previous turns
├─ Check cache for needed files
├─ Select read level (1-4) for each new read
└─ Proceed with current task

Middle of turn
├─ [CACHE:HIT] or [CACHE:MISS] per file
├─ [BUDGET:x/y] track reads
└─ [LOOP:n] check for loops

End of turn
├─ [PROGRESS] update
├─ Update [CONTEXT] memory
├─ Compress this turn's discussion
└─ [DECISION] update
```
