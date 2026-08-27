===================================================================
TELEGRAM CENTRAL BOT - INTERACTION & CRISIS SPECIFICATION
===================================================================
 INPUT PIPELINE RECEIVER
-------------------------------------------------------------------
- Monitor 'AI_Production_Agent' for final rendered video delivery.
- Fetch project payload metadata: {Project_ID, Title, Duration, Voice_Seed, BGM_Status}.
- Cache incoming media into the temporary container verification folder.

 INTERACTIVE INTERFACE WORKFLOW (The 3-Button Protocol)
-------------------------------------------------------------------
Upon receiving any video asset, the central bot MUST freeze automated deployment and construct a secure Telegram chat message attached with exactly 3 Inline Interactive Buttons:

🟢 BUTTON 1: [ 👍 مقبول ونشر / Approve & Publish ]
   - Payload Action: "CMD_TELEGRAM_APPROVE"
   - Operation: Trigger 'c2pa_validation.txt' execution pipeline.
   - Operation: Inject digital provenance credentials (EU AI Act Compliance).
   - Operation: Push the signed asset to 'publishing_module.txt' for immediate social distribution.
   - Operation: Invoke 'POST_PUBLISH_WIPE_PROTOCOL.md' upon success broadcast.

🔴 BUTTON 2: [ 👎 مرفوض وحذف / Reject & Wipe ]
   - Payload Action: "CMD_TELEGRAM_REJECT"
   - Operation: Flag project status as "Aborted" inside 'database_schema.py'.
   - Operation: Force terminate any current processing tasks linked to this Project_ID.
   - Operation: Invoke 'POST_PUBLISH_WIPE_PROTOCOL.md' immediately to execute permanent file shredding.

🟡 BUTTON 3: [ ✏️ تعديل وملاحظات / Granular Patching ]
   - Payload Action: "CMD_TELEGRAM_PATCH"
   - Operation: Display an inline Sub-Menu containing structured refinement presets:
     ├── [ 🔇 إلغاء الموسيقى ] ──> Sends: "PATCH:AUDIO:REMOVE_BGM"
     ├── [ 🗣️ تغيير المعلق ] ───> Sends: "PATCH:AUDIO:SWAP_VOICE"
     └── [ 👤 تغيير الأفاتار ] ──> Sends: "PATCH:VIDEO:SWAP_AVATAR"
   - Operation: Enable a text-input prompt for freeform manual feedback, to be routed back into 'AI_Writer_Agent'.

 TIMEOUT ENFORCEMENT & AUTONOMOUS PUBLISHING (TRUSTED BYPASS)
-------------------------------------------------------------------
- Start a strict 6-hour hardware countdown from the timestamp of message generation.
- CRITICAL LOGIC: Since the video has already passed all automated Islamic and EU Law compliance checks, it is considered safe for deployment.
- IF 6 hours expire with zero developer interaction:
  - System AUTONOMOUSLY executes "CMD_TELEGRAM_APPROVE".
  - Automatically inject digital credentials via 'c2pa_validation.txt'.
  - Deploy to social channels via 'publishing_module.txt' to maintain continuous channel growth.
===================================================================
