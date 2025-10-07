import { router } from "expo-router";
import { useState, useEffect } from "react";
import { Pressable, Switch, Text, TextInput, View, Image } from "react-native";
import { useDisplayName } from '@/hooks/useDisplayName';

// Function to generate a unique room name
const generateRoomName = () => {
  const timestamp = Date.now().toString(36);
  const randomStr = Math.random().toString(36).substring(2, 8);
  return `room-${timestamp}-${randomStr}`;
};

export default function JoinScreen() {
  const { displayName, isLoading } = useDisplayName();
  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);
  const [inviteAvatar, setInviteAvatar] = useState(true);

  const canJoin = displayName && displayName.trim().length > 0;

  const handleJoin = async () => {
    const roomName = generateRoomName();
    // For FE-only phase, just navigate with params.
    router.push({
      pathname: "/call",
      params: { room: roomName, name: displayName, mic: String(micOn), cam: String(camOn), avatar: String(inviteAvatar) },
    });
  };

  return (
    <View className="flex-1 items-center justify-center px-5 bg-[#0b0f16]">
      {/* Welcome Header */}
      <View className="items-center mb-8">
        {/* StudyMate Logo */}
        <View className="mb-6">
          <Image 
            source={require('../../assets/images/StudyMate Logo.png')}
            className="w-24 h-24 rounded-full"
            resizeMode="contain"
          />
        </View>
        
        <Text className="text-white text-3xl font-bold mb-2">
          Welcome back, {displayName || 'there'}! 👋
        </Text>
        <Text className="text-neutral-400 text-lg text-center">
          Ready to dive into an amazing call experience?
        </Text>
      </View>

      <View className="w-full gap-6">
        {/* Call Settings */}
        <View className="bg-neutral-800/30 rounded-2xl p-5">
          <Text className="text-white text-lg font-semibold mb-4">Call Settings</Text>
          
          <View className="space-y-4">
            <View className="flex-row items-center justify-between">
              <View className="flex-1">
                <Text className="text-neutral-300 text-base font-medium">Microphone</Text>
                <Text className="text-neutral-500 text-sm">Start with mic enabled</Text>
              </View>
              <Switch 
                value={micOn} 
                onValueChange={setMicOn}
                trackColor={{ false: "#374151", true: "#4f46e5" }}
                thumbColor={micOn ? "#ffffff" : "#9ca3af"}
              />
            </View>

            <View className="flex-row items-center justify-between">
              <View className="flex-1">
                <Text className="text-neutral-300 text-base font-medium">Camera</Text>
                <Text className="text-neutral-500 text-sm">Start with camera enabled</Text>
              </View>
              <Switch 
                value={camOn} 
                onValueChange={setCamOn}
                trackColor={{ false: "#374151", true: "#4f46e5" }}
                thumbColor={camOn ? "#ffffff" : "#9ca3af"}
              />
            </View>

            <View className="flex-row items-center justify-between">
              <View className="flex-1">
                <Text className="text-neutral-300 text-base font-medium">AI Assistant</Text>
                <Text className="text-neutral-500 text-sm">Invite AI avatar to join</Text>
              </View>
              <Switch 
                value={inviteAvatar} 
                onValueChange={setInviteAvatar}
                trackColor={{ false: "#374151", true: "#4f46e5" }}
                thumbColor={inviteAvatar ? "#ffffff" : "#9ca3af"}
              />
            </View>
          </View>
        </View>

        <Pressable
          onPress={handleJoin}
          disabled={!canJoin}
          className={`mt-8 rounded-2xl px-8 py-5 items-center shadow-lg ${
            canJoin 
              ? "bg-indigo-600" 
              : "bg-neutral-700"
          }`}
        >
          <Text className="text-white text-lg font-semibold">
            {canJoin ? "🚀 Start Your Call" : "Loading..."}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}
