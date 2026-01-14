1. Application-Breaking Issues

  1. Corrupted requirements.txt - backend/requirements.txt
    - File contains null bytes and missing dependencies (pymongo, python-dotenv, PyJWT)
    - App won't install or start
  2. Infinite Recursion in Auto-Save - frontend/helpers/store.js:707-721
    - saveWorkflowToV2() calls itself recursively forever
    - Causes memory leak and browser crash
  3. Missing Backend API Routes - backend/api_routes.py
    - Frontend calls /api/v2/projects/{id}, /api/v2/projects/{id}/workflows/{id}/execute
    - These routes don't exist - all CRUD operations fail with 404
  4. Global State Race Condition - backend/main.py:142
    - current_project is a global variable shared across all users
    - Multiple users will corrupt each other's workflow data
  5. Hardcoded localhost URL - frontend/contexts/AuthContext.tsx:83
    - Backend URL hardcoded to http://localhost:5001
    - Production deployments will fail

  2. Critical Security Vulnerabilities

  6. Debug Mode Enabled - backend/main.py:561
    - app.run(debug=True, host='0.0.0.0')
    - Exposes stack traces and enables remote code execution via Werkzeug debugger
  7. CORS Wildcard Configuration - backend/main.py:22
    - CORS(app) allows ALL origins
    - Any website can make requests to your API
  8. JWT Secret in Logs - backend/auth_middleware.py:21-23
    - Partial JWT secret printed to console
    - Security leak
  9. No Input Validation - Multiple files
    - User inputs directly used in MongoDB queries (NoSQL injection)
    - jsx_code in ReactBlock enables code injection
    - Block names vulnerable to XSS
  10. No Rate Limiting - All API routes
    - Vulnerable to DoS attacks and API abuse

  3. Data Loss & Corruption Issues

  11. User Creation Fails Silently - backend/user_service.py:99-104
    - Returns project that was never saved to database
    - Data loss
  12. Race Condition in MongoDB Updates - backend/user_service.py:300-334
    - Read-modify-write without atomic operations
    - Concurrent updates overwrite each other
  13. No Transaction Support
    - Multi-document updates not atomic
    - Partial failures leave inconsistent state

  HIGH PRIORITY BUGS

  4. Error Handling Issues

  14. Bare Except Clauses - backend/block_types/transform_block.py:68-69, 82-84
    - Empty except blocks hide all errors including KeyboardInterrupt
    - Silent failures impossible to debug
  15. Unhandled Promise Rejections - frontend/helpers/store.js:103-105, 236-238
    - API calls without .catch() or try-catch
    - Uncaught exceptions crash frontend
  16. No React Error Boundaries - frontend/app/**
    - Single component error crashes entire app
  17. Missing Error Handling in Execution - backend/main.py:144-169
    - No try-catch around execute_graph()
    - Unhandled exceptions crash server

  5. Database Issues

  18. Missing MongoDB Indexes - users collection
    - No index on supabase_user_id
    - Slow O(n) user lookups
    - Need: db.users.createIndex({ "supabase_user_id": 1 })
  19. N+1 Query Problem - backend/user_service.py:285-334
    - Fetches entire user document, iterates all projects
    - O(n²) complexity, degrades with scale
  20. No Schema Validation
    - Corrupt data can be inserted into MongoDB
    - No data integrity guarantees

  6. Type Safety Issues

  21. Mixed JS/TS Files - frontend/helpers/store.js, frontend/components/*.js
    - Critical files in JavaScript instead of TypeScript
    - No type checking, runtime errors
  22. Any Types Everywhere - frontend/services/projects.ts:16, 28-29
    - Loses all type safety benefits
    - No IntelliSense
  23. Missing Null Checks - frontend/helpers/store.js:79-82
    - Direct property access without optional chaining
    - Runtime null reference errors

  MEDIUM PRIORITY ISSUES

  7. Performance Issues

  24. Memory Leak - Unbounded Logs - frontend/helpers/store.js:500, 553, 572
    - Execution logs array grows indefinitely
    - Browser memory exhaustion
  25. No Debouncing on Auto-Save - frontend/helpers/store.js:707-721
    - Every keystroke creates setTimeout
    - Hundreds of pending timers
  26. Large State Cloning - frontend/helpers/store.js:245-253
    - Deep clones nodes array on every change
    - UI lag with large workflows

  8. API Design Issues

  27. Incorrect HTTP Status Codes - backend/main.py:277
    - Returns 200 for "not found" scenarios
    - Should return 404
  28. No Request Validation - backend/api_routes.py:19
    - request.json can be None
    - Causes TypeError crashes
  29. Missing Pagination - backend/api_routes.py:39-56
    - Returns ALL projects without limit
    - Performance degrades
  30. Inconsistent Response Formats
    - Some return {projects: [...]}, others {data: {projects: [...]}}
    - Frontend must handle multiple formats

  9. Configuration Issues

  31. No .env.example Files
    - No template for required environment variables
    - Setup failures for new developers
  32. No Environment Variable Validation
    - App starts without checking required vars
    - Cryptic runtime errors
  33. Missing Documentation for Required Env Vars
    - MONGODB_URI, SUPABASE_JWT_SECRET, MOORCHEH_API_KEY undocumented

  10. UI/UX Bugs

  34. Workflow Not Loaded on Refresh - frontend/app/workflow/page.js:43-49
    - useEffect dependencies don't trigger correctly
    - Blank canvas after page refresh
  35. No Loading States
    - No loading indicators during API calls
    - Users don't know if app is frozen
  36. No Confirmation Dialogs
    - No confirmation before deleting projects
    - Accidental deletions
  37. Optimistic Updates Without Rollback - frontend/helpers/store.js:245-253
    - UI shows changes that failed to save
    - No rollback mechanism
  38. Browser Alert for Input - frontend/helpers/store.js:540
    - window.prompt() blocks entire UI
    - Poor UX

  LOW PRIORITY (Code Quality)

  39. Dead Code - backend/main.py:514-543
    - Deprecated routes still present
    - Maintenance burden
  40. Duplicate Code - frontend/helpers/store.js:181-189, 219-238
    - Similar logic repeated
    - Bug fixes need double application
  41. Magic Numbers - Hardcoded values throughout
    - Can't configure timeouts, delays, etc.
  42. Inconsistent Naming - snake_case vs camelCase vs PascalCase
    - Causes confusion and transformation bugs
  43. Long Functions - backend/main.py:46-130
    - 84-line execute_graph() function
    - Hard to test and maintain
  44. Missing Documentation - All block types
    - No docstrings on functions
    - Hard to understand behavior

