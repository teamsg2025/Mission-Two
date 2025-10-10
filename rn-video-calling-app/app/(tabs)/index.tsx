import { router } from "expo-router";
import { useState, useEffect } from "react";
import { Pressable, Switch, Text, TextInput, View, Image, ScrollView } from "react-native";
import { Ionicons } from '@expo/vector-icons';
import { useDisplayName } from '@/hooks/useDisplayName';
import { useLanguage } from '@/hooks/useLanguage';

// Function to generate a unique room name
const generateRoomName = () => {
  const timestamp = Date.now().toString(36);
  const randomStr = Math.random().toString(36).substring(2, 8);
  return `room-${timestamp}-${randomStr}`;
};

export default function JoinScreen() {
  const { displayName, isLoading } = useDisplayName();
  const { selectedLanguage, setSelectedLanguage, languages } = useLanguage();
  const [micOn, setMicOn] = useState(true);
  const [camOn, setCamOn] = useState(true);
  const [inviteAvatar, setInviteAvatar] = useState(true);

  const canJoin = displayName && displayName.trim().length > 0;

  const handleJoin = async () => {
    const roomName = generateRoomName();
    // For FE-only phase, just navigate with params.
    router.push({
      pathname: "/call",
      params: { 
        room: roomName, 
        name: displayName, 
        mic: String(micOn), 
        cam: String(camOn), 
        avatar: String(inviteAvatar),
        language: selectedLanguage.code
      },
    });
  };

  return (
    <ScrollView className="flex-1 bg-[#0b0f16]" contentContainerStyle={{ flexGrow: 1 }}>
      <View className="flex-1 items-center justify-center px-5 py-8">
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
          
          {/* Language Selection */}
          <View className="mb-6">
            <Text className="text-neutral-300 text-base font-medium mb-3">AI Assistant Language</Text>
            <Text className="text-neutral-500 text-sm mb-4">Choose the language for your AI study assistant</Text>
            
            <View className="space-y-3">
              {languages.map((language) => (
                <Pressable
                  key={language.code}
                  onPress={() => setSelectedLanguage(language)}
                  className={`flex-row items-center justify-between p-4 rounded-xl border ${
                    selectedLanguage.code === language.code
                      ? 'border-indigo-500 bg-indigo-500/10'
                      : 'border-neutral-700 bg-neutral-800/50'
                  }`}
                >
                  <View className="flex-1">
                    <Text className="text-white text-base font-medium">
                      {language.nativeName}
                    </Text>
                    <Text className="text-neutral-400 text-sm">
                      {language.name}
                    </Text>
                  </View>
                  {selectedLanguage.code === language.code && (
                    <Ionicons name="checkmark-circle" size={24} color="#6366f1" />
                  )}
                </Pressable>
              ))}
            </View>
          </View>
          
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
    </ScrollView>
  );
}
