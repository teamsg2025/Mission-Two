import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native';
import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useRef } from 'react';
import { Platform } from 'react-native';
import 'react-native-reanimated';
import '../global.css';

// Initialize LiveKit globals for WebRTC
import { registerGlobals } from '@livekit/react-native';
registerGlobals();

import { useColorScheme } from '@/hooks/useColorScheme';
import PushNotificationService from '@/services/pushNotifications';
import * as Notifications from 'expo-notifications';

export default function RootLayout() {
  const colorScheme = useColorScheme();
  const [loaded] = useFonts({
    SpaceMono: require('../assets/fonts/SpaceMono-Regular.ttf'),
  });

  const notificationListener = useRef<Notifications.Subscription>();
  const responseListener = useRef<Notifications.Subscription>();

  useEffect(() => {
    // Initialize push notifications
    const initializePushNotifications = async () => {
      try {
        const pushService = PushNotificationService.getInstance();
        
        // Initialize with a default user ID (you can make this dynamic)
        const userId = 'user_' + Math.random().toString(36).substring(7);
        
        const success = await pushService.initialize(
          userId,
          // Notification received handler
          (notification) => {
            console.log('📱 Notification received in app:', notification);
            // Handle notification received while app is in foreground
          },
          // Notification response handler (user tapped notification)
          (response) => {
            console.log('📱 User tapped notification:', response);
            const data = response.notification.request.content.data;
            
            // Handle incoming call notification
            if (data?.type === 'incoming_call') {
              console.log('📞 Incoming call notification tapped');
              console.log('Call ID:', data.call_id);
              console.log('Room:', data.room_name);
              console.log('Caller:', data.caller_name);
              
              // TODO: Navigate to call screen with call data
              // This would require implementing the call screen first
            }
          }
        );

        if (success) {
          console.log('✅ Push notifications initialized successfully');
        } else {
          console.log('❌ Failed to initialize push notifications');
        }
      } catch (error) {
        console.error('❌ Error initializing push notifications:', error);
      }
    };

    if (loaded) {
      initializePushNotifications();
    }

    return () => {
      // Cleanup listeners
      if (notificationListener.current) {
        Notifications.removeNotificationSubscription(notificationListener.current);
      }
      if (responseListener.current) {
        Notifications.removeNotificationSubscription(responseListener.current);
      }
    };
  }, [loaded]);

  if (!loaded) {
    // Async font loading only occurs in development.
    return null;
  }

  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="+not-found" />
      </Stack>
      <StatusBar style="auto" />
    </ThemeProvider>
  );
}
