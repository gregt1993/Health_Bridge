# Health Bridge

**Health Bridge** is a custom integration for [Home Assistant](https://www.home-assistant.io/) that connects with the iOS app **[Health Assistant Link](https://apps.apple.com/us/app/health-assistant-link/id6745420767)** to bring your Apple Health data into your smart home.

---

## Installation

### 1. Install Health Assistant Link (iOS App)
To use this integration, you need the companion app installed on your iPhone:  
👉 [Download Health Assistant Link on the App Store](https://apps.apple.com/us/app/health-assistant-link/id6745420767)

### 2. Install Health Bridge via HACS
This integration is available in [HACS](https://hacs.xyz/), the Home Assistant Community Store.  
You must have HACS installed in your Home Assistant setup first.

Once HACS is installed, open the repository link below to add **Health Bridge** directly:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=health_bridge&owner=gregt1993)

---

## Setup

1. Install both the **iOS app** and the **Health Bridge** HACS integration.  
2. In the **Health Assistant Link** app, go to **Settings → Secret Token** and copy the generated token.  
3. In Home Assistant, configure the **Health Bridge** integration and **paste the same Secret Token**.  
   - ⚠️ The token must match **exactly** in both the iOS app and Home Assistant.  
4. Once matched, the integration will start syncing your Apple Health data automatically.

---

## Support

- 📱 [Health Assistant Link App](https://apps.apple.com/us/app/health-assistant-link/id6745420767)  
- 🛠 [HACS Integration: Health Bridge](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=health_bridge&owner=gregt1993)  
- 💬 Join the Home Assistant community for questions and troubleshooting.

---

## License
This project is licensed under the MIT License.



[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&repository=health_bridge&owner=gregt1993)
