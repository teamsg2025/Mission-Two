import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import Constants from 'expo-constants';

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export interface PushTokenData {
  expo_push_token: string;
  user_id?: string;
  device_name?: string;
}

export class PushNotificationService {
  private static instance: PushNotificationService;
  private expoPushToken: string | null = null;
  private notificationListener: any = null;
  private responseListener: any = null;

  private constructor() {}

  public static getInstance(): PushNotificationService {
    if (!PushNotificationService.instance) {
      PushNotificationService.instance = new PushNotificationService();
    }
    return PushNotificationService.instance;
  }

  /**
   * Register for push notifications and get Expo push token
   */
  public async registerForPushNotificationsAsync(): Promise<string | null> {
    if (!Device.isDevice) {
      console.log('Must use physical device for Push Notifications');
      return null;
    }

    try {
      // Check existing permissions
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      // Request permissions if not granted
      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        console.log('Failed to get push token for push notification!');
        return null;
      }

      // Get the Expo push token
      const token = (await Notifications.getExpoPushTokenAsync()).data;
      this.expoPushToken = token;
      console.log('📱 Expo Push Token:', token);

      // Configure Android notification channel
      if (Platform.OS === 'android') {
        await Notifications.setNotificationChannelAsync('default', {
          name: 'default',
          importance: Notifications.AndroidImportance.MAX,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: '#FF231F7C',
        });

        // Create incoming call channel
        await Notifications.setNotificationChannelAsync('incoming-call', {
          name: 'Incoming Calls',
          importance: Notifications.AndroidImportance.MAX,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: '#FF231F7C',
          sound: 'default',
        });
      }

      return token;
    } catch (error) {
      console.error('Error registering for push notifications:', error);
      return null;
    }
  }

  /**
   * Test server connectivity
   */
  public async testServerConnectivity(): Promise<boolean> {
    try {
      const API_URL = Constants.expoConfig?.extra?.apiUrl || 'https://mission-2-app-server.onrender.com';
      console.log('🔍 Testing server connectivity:', API_URL);
      
      const response = await fetch(`${API_URL}/`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      });
      
      console.log('🔍 Health check response status:', response.status);
      
      if (response.ok) {
        const result = await response.json();
        console.log('✅ Server is reachable:', result);
        return true;
      } else {
        console.error('❌ Server health check failed:', response.status);
        return false;
      }
    } catch (error) {
      console.error('❌ Server connectivity test failed:', error);
      return false;
    }
  }

  /**
   * Register the push token with the backend server
   */
  public async registerTokenWithServer(
    token: string,
    userId?: string,
    deviceName?: string
  ): Promise<boolean> {
    try {
      const API_URL = Constants.expoConfig?.extra?.apiUrl || 'https://mission-2-app-server.onrender.com';
      
      console.log('🔗 Attempting to register token with server:', API_URL);
      console.log('📱 Token:', token.substring(0, 20) + '...');
      console.log('👤 User ID:', userId);
      console.log('📱 Device:', deviceName || Device.deviceName || 'Unknown Device');
      
      const requestBody = {
        expo_push_token: token,
        user_id: userId,
        device_name: deviceName || Device.deviceName || 'Unknown Device',
      };
      
      console.log('📤 Request body:', JSON.stringify(requestBody, null, 2));
      
      const response = await fetch(`${API_URL}/register-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log('📡 Response status:', response.status);
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));

      if (response.ok) {
        const result = await response.json();
        console.log('✅ Token registered with server:', result);
        return true;
      } else {
        const errorText = await response.text();
        console.error('❌ Failed to register token with server:', response.status);
        console.error('❌ Error response:', errorText);
        return false;
      }
    } catch (error) {
      console.error('❌ Error registering token with server:', error);
      console.error('❌ Error type:', typeof error);
      console.error('❌ Error message:', error.message);
      console.error('❌ Error stack:', error.stack);
      return false;
    }
  }

  /**
   * Set up notification listeners
   */
  public setupNotificationListeners(
    onNotificationReceived?: (notification: Notifications.Notification) => void,
    onNotificationResponse?: (response: Notifications.NotificationResponse) => void
  ) {
    // Clean up existing listeners
    this.cleanup();

    // Notification received while app is in foreground
    this.notificationListener = Notifications.addNotificationReceivedListener(
      (notification) => {
        console.log('📱 Notification received:', notification);
        if (onNotificationReceived) {
          onNotificationReceived(notification);
        }
      }
    );

    // User tapped on notification
    this.responseListener = Notifications.addNotificationResponseReceivedListener(
      (response) => {
        console.log('📱 Notification response:', response);
        if (onNotificationResponse) {
          onNotificationResponse(response);
        }
      }
    );
  }

  /**
   * Clean up notification listeners
   */
  public cleanup() {
    if (this.notificationListener) {
      Notifications.removeNotificationSubscription(this.notificationListener);
      this.notificationListener = null;
    }
    if (this.responseListener) {
      Notifications.removeNotificationSubscription(this.responseListener);
      this.responseListener = null;
    }
  }

  /**
   * Get the current Expo push token
   */
  public getExpoPushToken(): string | null {
    return this.expoPushToken;
  }

  /**
   * Initialize push notifications (register + setup listeners)
   */
  public async initialize(
    userId?: string,
    onNotificationReceived?: (notification: Notifications.Notification) => void,
    onNotificationResponse?: (response: Notifications.NotificationResponse) => void
  ): Promise<boolean> {
    try {
      // Test server connectivity first
      console.log('🔍 Testing server connectivity before registration...');
      const serverReachable = await this.testServerConnectivity();
      if (!serverReachable) {
        console.warn('⚠️ Server is not reachable, but continuing with local registration');
      }

      // Register for push notifications
      const token = await this.registerForPushNotificationsAsync();
      if (!token) {
        return false;
      }

      // Register with server
      const registered = await this.registerTokenWithServer(token, userId);
      if (!registered) {
        console.warn('⚠️ Token registered locally but failed to register with server');
      }

      // Setup listeners
      this.setupNotificationListeners(onNotificationReceived, onNotificationResponse);

      return true;
    } catch (error) {
      console.error('❌ Error initializing push notifications:', error);
      return false;
    }
  }
}

export default PushNotificationService;

