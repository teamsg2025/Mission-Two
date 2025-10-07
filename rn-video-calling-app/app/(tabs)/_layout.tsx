import { Tabs } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { Ionicons } from '@expo/vector-icons';

export default function TabLayout() {
  return (
    <>
      <StatusBar style="light" />
      <Tabs
        screenOptions={{
          headerStyle: { backgroundColor: "#0b0f16" },
          headerTintColor: "white",
          headerTitleAlign: "center",
          tabBarStyle: { 
            backgroundColor: "#0b0f16",
            borderTopColor: "#1f2937",
            borderTopWidth: 1,
          },
          tabBarActiveTintColor: "#6366f1",
          tabBarInactiveTintColor: "#6b7280",
        }}
      >
        <Tabs.Screen
          name="index"
          options={{ 
            title: "Call",
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="call" size={size} color={color} />
            ),
            headerTitle: "StudyMate"
          }}
        />
        <Tabs.Screen
          name="profile"
          options={{ 
            title: "Profile",
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="person" size={size} color={color} />
            ),
            headerTitle: "Profile"
          }}
        />
      </Tabs>
    </>
  );
}
