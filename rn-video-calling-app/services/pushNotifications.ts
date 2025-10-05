import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import Constants from 'expo-constants';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

// Storage keys for persisting registration status
const STORAGE_KEYS = {
  PUSH_TOKEN_REGISTERED: 'push_token_registered',
  PUSH_TOKEN: 'push_token',
  USER_ID: 'user_id',
} as const;

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
   * Check if push token was already registered
   */
  private async isTokenAlreadyRegistered(): Promise<boolean> {
    try {
      const registered = await AsyncStorage.getItem(STORAGE_KEYS.PUSH_TOKEN_REGISTERED);
      return registered === 'true';
    } catch (error) {
      console.error('Error checking registration status:', error);
      return false;
    }
  }

  /**
   * Save registration status and token to storage
   */
  private async saveRegistrationStatus(token: string, userId?: string): Promise<void> {
    try {
      await AsyncStorage.multiSet([
        [STORAGE_KEYS.PUSH_TOKEN_REGISTERED, 'true'],
        [STORAGE_KEYS.PUSH_TOKEN, token],
        [STORAGE_KEYS.USER_ID, userId || ''],
      ]);
      console.log('✅ Registration status saved to storage');
    } catch (error) {
      console.error('Error saving registration status:', error);
    }
  }

  /**
   * Get stored push token
   */
  private async getStoredToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(STORAGE_KEYS.PUSH_TOKEN);
    } catch (error) {
      console.error('Error getting stored token:', error);
      return null;
    }
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
      const API_URL = Constants.expoConfig?.extra?.apiUrl || 'https://mission-two-server.onrender.com';
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
      const API_URL = Constants.expoConfig?.extra?.apiUrl || 'https://mission-two-server.onrender.com';
      
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
   * Reset registration status (useful for testing or re-registration)
   */
  public async resetRegistrationStatus(): Promise<void> {
    try {
      await AsyncStorage.multiRemove([
        STORAGE_KEYS.PUSH_TOKEN_REGISTERED,
        STORAGE_KEYS.PUSH_TOKEN,
        STORAGE_KEYS.USER_ID,
      ]);
      this.expoPushToken = null;
      console.log('✅ Registration status reset');
    } catch (error) {
      console.error('Error resetting registration status:', error);
    }
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
      // Check if token was already registered
      const alreadyRegistered = await this.isTokenAlreadyRegistered();
      
      if (alreadyRegistered) {
        console.log('📱 Push token already registered, skipping registration');
        console.log('📱 This means the app was previously installed and token was registered');
        
        // Get the stored token
        const storedToken = await this.getStoredToken();
        if (storedToken) {
          this.expoPushToken = storedToken;
          console.log('📱 Using stored push token:', storedToken.substring(0, 20) + '...');
        }
        
        // Setup listeners only (no registration needed)
        this.setupNotificationListeners(onNotificationReceived, onNotificationResponse);
        return true;
      }

      console.log('📱 First time registration, proceeding with push token registration...');

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

      // Save registration status to prevent future registrations
      console.log('📱 Saving registration status to prevent future registrations...');
      await this.saveRegistrationStatus(token, userId);

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

