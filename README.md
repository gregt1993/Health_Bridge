# Health Bridge

<p align="center">
  <img src="https://is1-ssl.mzstatic.com/image/thumb/Purple221/v4/8c/0a/b3/8c0ab330-3e85-27b2-8532-e1f912c29fb6/AppIcon-0-0-1x_U007ephone-0-1-85-220.png/460x0w.webp" alt="Health Assistant Link Icon" width="120"/>
  <img src="https://is1-ssl.mzstatic.com/image/thumb/PurpleSource221/v4/77/b8/20/77b82043-ced8-8c60-fc24-a92c09aa53a6/Placeholder.mill/1024x1024bb.png" alt="Phone Assistant Link Icon" width="120"/>
</p>

<p align="center">
  🌐 <a href="https://healthassistantlink.com"><b>healthassistantlink.com</b></a>
  &nbsp;•&nbsp;
  📱 <a href="https://apps.apple.com/us/app/health-assistant-link/id6745420767">App Store</a>
  &nbsp;•&nbsp;
  📚 <a href="https://healthassistantlink.com/stories">User Stories</a>
</p>

> [!TIP]
> ### 🆕 Meet **Phone Assistant Link** — Screen Time and App Blocking, now in Home Assistant
> A brand-new companion app that brings **Apple Screen Time** into your smart home. Block apps and app groups, set daily usage limits, and apply temporary allow/block overrides — all from Home Assistant, with usage and "blocked opens" surfaced as sensors.
>
> ✨ Uses the **same Health Bridge integration** — just pick **Phone Assistant Link** during setup.
> 📱 _App Store — [Download Now](https://apps.apple.com/nz/app/phone-assistant-link/id6806541422)._

**Health Bridge** is a custom integration for [Home Assistant](https://www.home-assistant.io/) that connects with the companion iOS apps **[Health Assistant Link](https://apps.apple.com/us/app/health-assistant-link/id6745420767)** (Apple Health → Home Assistant) and the new **Phone Assistant Link** (Apple Screen Time → Home Assistant) to bring your iPhone data into your smart home.

> 🆓 **Free to use.** Health Assistant Link is free to download and use to sync your Apple Health data into Home Assistant. An optional paid upgrade unlocks **automated syncing**, so your data keeps updating in the background without manual taps.

---

## 💡 Recommendations

For the most reliable syncing:

- Keep **both** the **Health Assistant Link** iPhone app **and** the **Apple Watch app** open in the background.
- Use **Shortcuts** to schedule automatic syncs at **8:00 AM**, **4:00 PM**, and **12:00 AM**.
- Aim to open the app at least once per day (this can be easily done as part of a "sleep mode" shortcut).
- Add one of the lock screen widgets 

This setup creates optimal conditions for consistent, regular syncing of your Apple Health data to Home Assistant.

> 💡 Want ideas? See how others use their data in our [User Stories](https://healthassistantlink.com/stories).

---

## 🚀 Installation


### 1. Install Health Assistant Link (iOS App)
You’ll need the companion iOS app installed on your iPhone:  
👉 [Download Health Assistant Link on the App Store](https://apps.apple.com/us/app/health-assistant-link/id6745420767)

The app is **free to use**. Automated syncing is available as an optional paid upgrade.

### 2. Install Health Bridge via HACS
This integration is available in [HACS](https://hacs.xyz/). You must have HACS set up in your Home Assistant instance first.

Once HACS is installed, add **Health Bridge** using the repository link below:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=health_bridge&owner=gregt1993)

---

## ⚙️ Setup

### Home Assistant Setup
1. Install the **Health Bridge** integration from HACS.  
   <img width="600" alt="image" src="https://github.com/user-attachments/assets/33c515ff-9a2f-4318-86e8-6226b8699a39" />

2. Add the repository in HACS.  
   <img width="600" alt="image" src="https://github.com/user-attachments/assets/f44d9f65-05b1-48c7-ac29-0a1b1356fed6" />

3. Download the integration.  
   <img width="600" alt="image" src="https://github.com/user-attachments/assets/d9382fec-2673-4b3a-921f-d625fa5770ae" />

4. Restart Home Assistant.  
   <img width="600" alt="image" src="https://github.com/user-attachments/assets/582cf776-f3d2-479c-9e28-c76317be4c65" />

5. In the **Integrations** menu, click **Add Entry**, select if you're setting up Health Assistant Link or Phone Assistant Link, enter a secret token, and submit.

---

### iOS App Setup
1. Open the **Health Assistant Link** app.  
   👉 [Download here](https://apps.apple.com/us/app/health-assistant-link/id6745420767) if not already installed.  
<img width="250" alt="Screenshot iPhone 17 Pro 02-09-2026 at 9 24 29 PM" src="https://github.com/user-attachments/assets/29aeddc6-b7a9-498a-8199-30998689d1e6" />


2. Accept all required permissions.  
   <img width="250" alt="Screenshot iPhone 17 Pro 02-09-2026 at 9 24 34 PM" src="https://github.com/user-attachments/assets/08d9d91b-ce51-4fa8-a650-953bccf4b163" />
   <img width="250" alt="IMG_5529" src="https://github.com/user-attachments/assets/14880e0a-cb44-4850-8f76-bfa2f7e68a28" />

3. Enter your **Home Assistant external URL**, your name, and the secret token you created earlier.   
   <img width="250" alt="Screenshot iPhone 17 Pro 02-09-2026 at 9 25 03 PM" src="https://github.com/user-attachments/assets/99495bfb-1ec9-4c30-a44b-eb5a9644d409" />


4. Test the connection to confirm the URL is correct.
   
   <img width="250" alt="Screenshot iPhone 17 Pro 02-09-2026 at 9 25 08 PM" src="https://github.com/user-attachments/assets/e3aa1b17-c40b-4b96-99a4-0f8a544fd060" />

6. **(Optional) Upgrade for automated syncing.** The app is free to use with manual syncing. If you’d like your data to sync automatically in the background, subscribe to the optional automated syncing upgrade.  
   <img width="250" alt="Screenshot iPhone 17 Pro 02-09-2026 at 9 25 18 PM" src="https://github.com/user-attachments/assets/0e961ba1-320b-498d-950e-a49057268870" />
   
7. Tap **Sync Now** to start syncing. Leaving the app open in the background improves reliability.    
   
   <img width="250" alt="Screenshot iPhone 17 Pro 02-09-2026 at 9 27 27 PM" src="https://github.com/user-attachments/assets/b1d6c500-9de5-4a70-a5a8-541c9ea94c03" />



---

## 📱 Phone Assistant Link (Screen Time)

**Phone Assistant Link** is a separate companion app that uses the **same Health Bridge integration** to bring **Apple Screen Time** controls into Home Assistant. Instead of health data, it exposes app-restriction and usage entities you can automate.

**What you can do from Home Assistant:**
- 🔒 **Block apps & app groups** — flip a switch to shield selected apps.
- ⏳ **Daily usage limits** — set a per-group allowance; the app auto-blocks when it's reached.
- ⏱️ **Temporary overrides** — apply a timed allow/block that expires on its own.
- 📊 **Usage sensors** — approximate, privacy-preserving screen-time minutes per app/group.
- 🚫 **Blocked-opens sensors** — an approximate daily count of how often a blocked app was opened (resets daily).

**Setup:** identical to the steps above — install Health Bridge via HACS, add an entry and choose **Phone Assistant Link** in step 5, then enter your Home Assistant URL and secret token in the app.

> ℹ️ **Privacy note:** Screen Time metrics are approximate by design. Apple's on-device APIs keep app identities private and don't expose exact open counts, so usage minutes and blocked-opens are best read as trends rather than precise figures.

📱 _Phone Assistant Link — App Store coming soon._

---

## 🆘 Support

- 🌐 [Website: healthassistantlink.com](https://healthassistantlink.com)  
- 📱 [Health Assistant Link App](https://apps.apple.com/us/app/health-assistant-link/id6745420767)  
- 🛠 [HACS Integration: Health Bridge](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=health_bridge&owner=gregt1993)  
- 📚 [User Stories & guides](https://healthassistantlink.com/stories)  
- 💬 Join the Home Assistant community for troubleshooting and discussion.

---

## Community Projects

- 📊 Check out this Dashboard card by BrainDeLook: https://github.com/BrainDeLook/health-bridge-dashboard-card

---

## 📄 License
This project is licensed under the MIT License.
