# Character Flow QA Checklist

This checklist validates the current Godot account-shell character flow.

## Preconditions
- Latest released build installed.
- Backend reachable and healthy.
- Test account with admin privileges (`admin`) and one non-admin account.

## Scenario Matrix

### 1. Empty Account Path
1. Log in with an account that has no characters.
2. Confirm default post-login screen is `Character List`.
3. Confirm empty-state message is visible in roster.
4. Open `Create Character`, create one character, and verify success.
5. Confirm return to `Character List` and new character appears.

### 2. Single Character Path
1. Log in with account that has exactly one character.
2. Confirm character card appears in roster and is selectable.
3. Confirm center preview updates when the card is selected.
4. Confirm right panel details match selected character metadata.
5. Click `Play` and verify gameplay session starts.

### 3. Multi-Character Path
1. Ensure account has at least three characters.
2. Use roster search input to filter by:
   - partial name,
   - level/location text.
3. Confirm roster updates deterministically and selection remains stable.
4. Clear search and confirm full roster restores.
5. Delete a selected character and verify roster auto-refreshes.

### 4. Admin Spawn Override Path
1. Log in as admin.
2. Select a character and confirm spawn override dropdown appears in right panel.
3. Choose a level override and click `Play`.
4. Verify spawn follows override target.
5. Reset dropdown to `Current location` and verify default spawn behavior returns.

### 5. MFA + Auth UX Path
1. Open settings -> security.
2. Toggle MFA ON and verify inline QR/info renders.
3. Toggle MFA OFF and verify login works without OTP.
4. On auth screen, validate Tab/Shift+Tab focus order:
   - login mode: email -> password -> otp -> login -> create account -> exit
   - register mode: display name -> email -> password -> register -> back -> exit
5. Confirm auth panel sizing is compact and does not dominate vertical viewport.
