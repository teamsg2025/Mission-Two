export default {
  expo: {
    name: "rn-video-calling-app",
    slug: "rn-video-calling-app",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/images/icon.png",
    scheme: "rn-video-calling-app",
    userInterfaceStyle: "automatic",
    newArchEnabled: false,
    ios: {
      supportsTablet: true,
      infoPlist: {
        NSCameraUsageDescription: "This app uses the camera for video calls.",
        NSMicrophoneUsageDescription: "This app uses the microphone for calls.",
      },
    },
    android: {
      googleServicesFile: process.env.GOOGLE_SERVICES_JSON,
      edgeToEdgeEnabled: true,
      adaptiveIcon: {
        foregroundImage: "./assets/images/adaptive-icon.png",
        backgroundColor: "#ffffff",
      },
      permissions: [
        "INTERNET",
        "CAMERA",
        "RECORD_AUDIO",
        "BLUETOOTH",
        "BLUETOOTH_CONNECT",
        "MODIFY_AUDIO_SETTINGS",
      ],
      package: "com.anonymous.rnvideocallingapp",
    },
    web: {
      bundler: "metro",
      output: "static",
      favicon: "./assets/images/favicon.png",
    },
    plugins: [
      "expo-router",
      [
        "expo-splash-screen",
        {
          image: "./assets/images/splash-icon.png",
          imageWidth: 200,
          resizeMode: "contain",
          backgroundColor: "#ffffff",
        },
      ],
      [
        "react-native-permissions",
        {
          iosPermissions: ["Camera", "Microphone"],
          androidPermissions: [
            "android.permission.CAMERA",
            "android.permission.RECORD_AUDIO",
            "android.permission.BLUETOOTH_CONNECT",
          ],
        },
      ],
      [
        "expo-notifications",
        {
          icon: "./assets/images/icon.png",
          color: "#ffffff",
          defaultChannel: "default",
        },
      ],
      "@livekit/react-native-expo-plugin",
    ],
    experiments: {
      typedRoutes: true,
    },
    extra: {
      router: {},
      apiUrl: "https://mission-two-server.onrender.com",
      eas: {
        projectId: "c6ccc88a-4f42-4b4b-97f2-7b1860ed5bc6",
      },
    },
    "owner": "funaiorg",
  },
};
