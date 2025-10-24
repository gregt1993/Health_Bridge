# Health Bridge

<p align="center">
  <img src="https://is1-ssl.mzstatic.com/image/thumb/Purple221/v4/8c/0a/b3/8c0ab330-3e85-27b2-8532-e1f912c29fb6/AppIcon-0-0-1x_U007ephone-0-1-85-220.png/460x0w.webp" alt="Health Assistant Link Icon" width="120"/>
</p>

**Health Bridge** is a custom integration for [Home Assistant](https://www.home-assistant.io/) that connects with the iOS app **[Health Assistant Link](https://apps.apple.com/us/app/health-assistant-link/id6745420767)** to bring your Apple Health data into your smart home.

---

## 💡 Recommendations

For the most reliable syncing:

- Keep **both** the **Health Assistant Link** iPhone app **and** the **Apple Watch app** open in the background.
- Use **Shortcuts** to schedule automatic syncs at **8:00 AM**, **4:00 PM**, and **12:00 AM**.

This setup creates optimal conditions for consistent, regular syncing of your Apple Health data to Home Assistant.

---

## 🚀 Installation

### 1. Install Health Assistant Link (iOS App)
You’ll need the companion iOS app installed on your iPhone:  
👉 [Download Health Assistant Link on the App Store](https://apps.apple.com/us/app/health-assistant-link/id6745420767)

### 2. Install Health Bridge via HACS
This integration is available in [HACS](https://hacs.xyz/). You must have HACS set up in your Home Assistant instance first.

Once HACS is installed, add **Health Bridge** using the repository link below:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=health_bridge&owner=gregt1993)

---

## ⚙️ Setup

### Home Assistant Setup
1. Install the **Health Bridge** integration from HACS.  
   <img width="1333" height="862" alt="image" src="https://github.com/user-attachments/assets/33c515ff-9a2f-4318-86e8-6226b8699a39" />

2. Add the repository in HACS.  
   <img width="1340" height="862" alt="image" src="https://github.com/user-attachments/assets/f44d9f65-05b1-48c7-ac29-0a1b1356fed6" />

3. Download the integration.  
   <img width="1341" height="868" alt="image" src="https://github.com/user-attachments/assets/d9382fec-2673-4b3a-921f-d625fa5770ae" />

4. Restart Home Assistant.  
   <img width="1335" height="863" alt="image" src="https://github.com/user-attachments/assets/582cf776-f3d2-479c-9e28-c76317be4c65" />

5. In the **Integrations** menu, click **Add Entry**, enter a secret token, and submit.

---

### iOS App Setup
1. Open the **Health Assistant Link** app.  
   👉 [Download here](https://apps.apple.com/us/app/health-assistant-link/id6745420767) if not already installed.  
   <img width="590" height="1278" alt="IMG_5527" src="https://github.com/user-attachments/assets/fd5b5b1b-417d-41eb-ac07-3ccd97ddf812" />

2. Accept all required permissions.  
   <img width="590" height="1278" alt="IMG_5528" src="https://github.com/user-attachments/assets/b575de6a-e0b9-4c0b-82a7-47694aed3a10" />  
   <img width="590" height="1278" alt="IMG_5529" src="https://github.com/user-attachments/assets/14880e0a-cb44-4850-8f76-bfa2f7e68a28" />

3. Select the health data you want to sync (more can be added later). 
   <img width="590" height="1278" alt="IMG_5530" src="https://github.com/user-attachments/assets/bac73a50-8c55-4359-8599-2fd00d069313" />

4. Enter your **Home Assistant external URL**, your name, and the secret token you created earlier.   
   <img width="590" height="1278" alt="IMG_5532" src="https://github.com/user-attachments/assets/bf032b47-1387-4878-9a09-83c24422bc7c" />

5. Test the connection to confirm the URL is correct.  
   <img width="590" height="1278" alt="IMG_5531" src="https://github.com/user-attachments/assets/7eec01ec-9a52-4b5f-b576-04a6a5856587" />
   <img width="590" height="1278" alt="IMG_5533" src="https://github.com/user-attachments/assets/d2c382d0-418b-45fa-9b6c-1a5c9bec24b4" />

6. Start your **1-week free trial** and subscribe.  
   
   <img width="590" height="1278" alt="IMG_5534" src="https://github.com/user-attachments/assets/371623e6-6b7b-4a07-bb68-c3b9f7f38149" />

8. Restart to regester the subsription with the app (close the app out of multi-tasking, then re-open)
   
   <img width="590" height="1278" alt="IMG_5535" src="https://github.com/user-attachments/assets/2aff6498-a6db-4c79-81af-a276ae195396" />

9. Tap **Sync Now** to start syncing. Leaving the app open in the background improves reliability.    
   
   <img width="590" height="1278" alt="IMG_5538" src="https://github.com/user-attachments/assets/e5feef16-4148-41d4-8985-3367581cfb5e" />




---

## 🆘 Support

- 📱 [Health Assistant Link App](https://apps.apple.com/us/app/health-assistant-link/id6745420767)  
- 🛠 [HACS Integration: Health Bridge](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=health_bridge&owner=gregt1993)  
- 💬 Join the Home Assistant community for troubleshooting and discussion.

---

## 📄 License
This project is licensed under the MIT License.
