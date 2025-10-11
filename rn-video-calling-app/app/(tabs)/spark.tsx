import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useDisplayName } from '@/hooks/useDisplayName';

const API_BASE_URL = 'https://mission-two-server.onrender.com';

interface User {
  id: string;
  display_name: string;
}

interface ConversationStarters {
  starters: string[];
  user_info: string;
  memory_count?: number;
  error?: string;
}

export default function SparkScreen() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [starters, setStarters] = useState<string[]>([]);
  const [loadingStarters, setLoadingStarters] = useState(false);
  const { displayName } = useDisplayName();

  useEffect(() => {
    fetchUsers();
  }, [displayName]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/users`);
      const data = await response.json();
      
      // Filter out current user
      const otherUsers = data.users.filter((user: User) => user.display_name !== displayName);
      setUsers(otherUsers);
    } catch (error) {
      console.error('Error fetching users:', error);
      Alert.alert('Error', 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchUsers();
    setRefreshing(false);
  };

  const handleUserSelect = async (user: User) => {
    setSelectedUser(user);
    setStarters([]);
    setLoadingStarters(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/conversation-starters`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          display_name: user.display_name,
        }),
      });

      const data: ConversationStarters = await response.json();
      setStarters(data.starters);
    } catch (error) {
      console.error('Error fetching conversation starters:', error);
      Alert.alert('Error', 'Failed to generate conversation starters');
      setStarters([
        "Hey! How's your studying going?",
        "What subjects are you working on?",
        "Need any study help?",
      ]);
    } finally {
      setLoadingStarters(false);
    }
  };

  const handleBack = () => {
    setSelectedUser(null);
    setStarters([]);
  };

  const copyToClipboard = (text: string) => {
    Alert.alert('Copied!', text);
  };

  if (loading) {
    return (
      <View className="flex-1 bg-[#0b0f16] items-center justify-center">
        <ActivityIndicator size="large" color="#6366f1" />
        <Text className="text-gray-400 mt-4">Loading users...</Text>
      </View>
    );
  }

  if (selectedUser) {
    return (
      <View className="flex-1 bg-[#0b0f16]">
        <View className="p-4 border-b border-gray-800">
          <TouchableOpacity onPress={handleBack} className="flex-row items-center mb-4">
            <Ionicons name="arrow-back" size={24} color="#6366f1" />
            <Text className="text-white ml-2 text-lg font-semibold">Back to Users</Text>
          </TouchableOpacity>
          
          <View className="bg-gray-900 p-4 rounded-lg">
            <Text className="text-xl font-bold text-white mb-1">
              {selectedUser.display_name}
            </Text>
            <Text className="text-gray-400 text-sm">
              Start a conversation with them!
            </Text>
          </View>
        </View>

        <ScrollView className="flex-1 p-4">
          <Text className="text-gray-300 text-lg font-semibold mb-4">
            💬 Conversation Starters
          </Text>

          {loadingStarters ? (
            <View className="items-center py-8">
              <ActivityIndicator size="large" color="#6366f1" />
              <Text className="text-gray-400 mt-4">Generating questions...</Text>
            </View>
          ) : (
            starters.map((starter, index) => (
              <TouchableOpacity
                key={index}
                onPress={() => copyToClipboard(starter)}
                className="bg-gray-900 p-4 rounded-lg mb-3 border border-gray-800"
                activeOpacity={0.7}
              >
                <View className="flex-row items-start">
                  <View className="bg-indigo-600 w-8 h-8 rounded-full items-center justify-center mr-3 mt-0.5">
                    <Text className="text-white font-bold">{index + 1}</Text>
                  </View>
                  <Text className="text-white flex-1 text-base leading-6">
                    {starter}
                  </Text>
                </View>
              </TouchableOpacity>
            ))
          )}

          <View className="bg-gray-900 p-4 rounded-lg mt-4">
            <Text className="text-gray-400 text-sm">
              💡 Tip: These questions are personalized based on their study history.
              Tap any question to copy it!
            </Text>
          </View>
        </ScrollView>
      </View>
    );
  }

  return (
    <View className="flex-1 bg-[#0b0f16]">
      <View className="p-4 bg-gray-900 border-b border-gray-800">
        <Text className="text-white text-lg font-semibold mb-2">
          🤝 Connect with Study Buddies
        </Text>
        <Text className="text-gray-400 text-sm">
          Select a user to get personalized conversation starters based on their study sessions
        </Text>
      </View>

      {users.length === 0 ? (
        <View className="flex-1 items-center justify-center p-8">
          <Ionicons name="people-outline" size={80} color="#6b7280" />
          <Text className="text-gray-400 text-center mt-4 text-lg">
            No other users found yet
          </Text>
          <Text className="text-gray-500 text-center mt-2">
            When other students use StudyMate, they'll appear here!
          </Text>
          <TouchableOpacity
            onPress={onRefresh}
            className="mt-6 bg-indigo-600 px-6 py-3 rounded-lg"
          >
            <Text className="text-white font-semibold">Refresh</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView
          className="flex-1"
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#6366f1']} />
          }
        >
          <View className="p-4">
            <Text className="text-gray-300 text-sm mb-4">
              {users.length} {users.length === 1 ? 'user' : 'users'} available
            </Text>

            {users.map((user) => (
              <TouchableOpacity
                key={user.id}
                onPress={() => handleUserSelect(user)}
                className="bg-gray-900 p-4 rounded-lg mb-3 border border-gray-800 flex-row items-center"
                activeOpacity={0.7}
              >
                <View className="bg-indigo-600 w-12 h-12 rounded-full items-center justify-center mr-4">
                  <Ionicons name="person" size={24} color="white" />
                </View>
                <View className="flex-1">
                  <Text className="text-white font-semibold text-lg mb-1">
                    {user.display_name}
                  </Text>
                  <Text className="text-gray-400 text-sm">
                    Tap to generate conversation starters
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={24} color="#6b7280" />
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      )}
    </View>
  );
}
