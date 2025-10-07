import { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const DISPLAY_NAME_KEY = 'user_display_name';

export function useDisplayName() {
  const [displayName, setDisplayName] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  // Load display name from storage on mount
  useEffect(() => {
    loadDisplayName();
  }, []);

  const loadDisplayName = async () => {
    try {
      const storedName = await AsyncStorage.getItem(DISPLAY_NAME_KEY);
      if (storedName) {
        setDisplayName(storedName);
      } else {
        // Set default name if none exists
        setDisplayName('abel');
      }
    } catch (error) {
      console.error('Error loading display name:', error);
      setDisplayName('abel');
    } finally {
      setIsLoading(false);
    }
  };

  const saveDisplayName = async (name: string) => {
    try {
      await AsyncStorage.setItem(DISPLAY_NAME_KEY, name);
      setDisplayName(name);
      console.log('Display name saved:', name);
    } catch (error) {
      console.error('Error saving display name:', error);
    }
  };

  const clearDisplayName = async () => {
    try {
      await AsyncStorage.removeItem(DISPLAY_NAME_KEY);
      setDisplayName('abel');
    } catch (error) {
      console.error('Error clearing display name:', error);
    }
  };

  return {
    displayName,
    setDisplayName: saveDisplayName,
    clearDisplayName,
    isLoading
  };
}
