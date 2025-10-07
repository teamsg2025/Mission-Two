import { useState, useEffect } from "react";
import { View, Text, TextInput, Pressable, Switch, Alert, ScrollView } from "react-native";
import { Ionicons } from '@expo/vector-icons';
import { useDisplayName } from '@/hooks/useDisplayName';

export default function ProfileScreen() {
  const { displayName, setDisplayName, isLoading } = useDisplayName();
  const [name, setName] = useState(displayName);
  const [email, setEmail] = useState("abel@example.com");
  const [bio, setBio] = useState("AI Study Assistant");
  const [notifications, setNotifications] = useState(true);
  const [micEnabled, setMicEnabled] = useState(true);
  const [cameraEnabled, setCameraEnabled] = useState(true);
  const [avatarEnabled, setAvatarEnabled] = useState(true);

  // Sync local state with stored display name
  useEffect(() => {
    if (!isLoading && displayName) {
      setName(displayName);
    }
  }, [displayName, isLoading]);

  const handleSave = async () => {
    try {
      await setDisplayName(name);
      Alert.alert("Profile Updated", "Your profile has been saved successfully!");
    } catch (error) {
      Alert.alert("Error", "Failed to save profile. Please try again.");
    }
  };

  return (
    <ScrollView className="flex-1 bg-[#0b0f16]">
      <View className="px-5 py-6">
        {/* Profile Header */}
        <View className="items-center mb-8">
          <View className="w-24 h-24 rounded-full bg-indigo-600 items-center justify-center mb-4">
            <Ionicons name="person" size={40} color="white" />
          </View>
          <Text className="text-white text-2xl font-semibold">{name}</Text>
          <Text className="text-neutral-400 text-base">{email}</Text>
        </View>

        {/* Basic Information */}
        <View className="mb-6">
          <Text className="text-white text-lg font-semibold mb-4">Basic Information</Text>
          
          <View className="mb-4">
            <Text className="text-neutral-300 mb-2">Display Name</Text>
            <TextInput
              value={name}
              onChangeText={setName}
              placeholder="Enter your name"
              placeholderTextColor="#6b7280"
              className="border border-neutral-700 rounded-xl px-4 py-3 text-white bg-neutral-800"
            />
          </View>

          <View className="mb-4">
            <Text className="text-neutral-300 mb-2">Email</Text>
            <TextInput
              value={email}
              onChangeText={setEmail}
              placeholder="Enter your email"
              placeholderTextColor="#6b7280"
              className="border border-neutral-700 rounded-xl px-4 py-3 text-white bg-neutral-800"
              keyboardType="email-address"
            />
          </View>

          <View className="mb-4">
            <Text className="text-neutral-300 mb-2">Bio</Text>
            <TextInput
              value={bio}
              onChangeText={setBio}
              placeholder="Tell us about yourself"
              placeholderTextColor="#6b7280"
              className="border border-neutral-700 rounded-xl px-4 py-3 text-white bg-neutral-800"
              multiline
              numberOfLines={3}
            />
          </View>
        </View>

        {/* Call Settings */}
        <View className="mb-6">
          <Text className="text-white text-lg font-semibold mb-4">Call Settings</Text>
          
          <View className="flex-row items-center justify-between mb-4">
            <View className="flex-1">
              <Text className="text-neutral-300">Microphone Enabled</Text>
              <Text className="text-neutral-500 text-sm">Start calls with mic on</Text>
            </View>
            <Switch 
              value={micEnabled} 
              onValueChange={setMicEnabled}
              trackColor={{ false: "#374151", true: "#4f46e5" }}
              thumbColor={micEnabled ? "#ffffff" : "#9ca3af"}
            />
          </View>

          <View className="flex-row items-center justify-between mb-4">
            <View className="flex-1">
              <Text className="text-neutral-300">Camera Enabled</Text>
              <Text className="text-neutral-500 text-sm">Start calls with camera on</Text>
            </View>
            <Switch 
              value={cameraEnabled} 
              onValueChange={setCameraEnabled}
              trackColor={{ false: "#374151", true: "#4f46e5" }}
              thumbColor={cameraEnabled ? "#ffffff" : "#9ca3af"}
            />
          </View>

          <View className="flex-row items-center justify-between mb-4">
            <View className="flex-1">
              <Text className="text-neutral-300">AI Avatar</Text>
              <Text className="text-neutral-500 text-sm">Invite AI assistant to calls</Text>
            </View>
            <Switch 
              value={avatarEnabled} 
              onValueChange={setAvatarEnabled}
              trackColor={{ false: "#374151", true: "#4f46e5" }}
              thumbColor={avatarEnabled ? "#ffffff" : "#9ca3af"}
            />
          </View>
        </View>

        {/* Notifications */}
        <View className="mb-8">
          <Text className="text-white text-lg font-semibold mb-4">Notifications</Text>
          
          <View className="flex-row items-center justify-between">
            <View className="flex-1">
              <Text className="text-neutral-300">Push Notifications</Text>
              <Text className="text-neutral-500 text-sm">Receive call notifications</Text>
            </View>
            <Switch 
              value={notifications} 
              onValueChange={setNotifications}
              trackColor={{ false: "#374151", true: "#4f46e5" }}
              thumbColor={notifications ? "#ffffff" : "#9ca3af"}
            />
          </View>
        </View>

        {/* Save Button */}
        <Pressable
          onPress={handleSave}
          className="bg-indigo-600 rounded-2xl px-5 py-4 items-center mb-6"
        >
          <Text className="text-white text-base font-medium">Save Profile</Text>
        </Pressable>

        {/* App Info */}
        <View className="items-center">
          <Text className="text-neutral-500 text-sm">StudyMate v1.0.0</Text>
        </View>
      </View>
    </ScrollView>
  );
}
