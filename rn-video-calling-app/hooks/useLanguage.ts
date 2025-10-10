import { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const LANGUAGE_KEY = 'user_language';

export interface Language {
  code: string;
  name: string;
  nativeName: string;
}

export const LANGUAGES: Language[] = [
  { code: 'en-US', name: 'English', nativeName: 'English' },
  { code: 'cmn-CN', name: 'Chinese', nativeName: '中文' }
];

export function useLanguage() {
  const [selectedLanguage, setSelectedLanguage] = useState<Language>(LANGUAGES[0]);
  const [isLoading, setIsLoading] = useState(true);

  // Load language from storage on mount
  useEffect(() => {
    loadLanguage();
  }, []);

  const loadLanguage = async () => {
    try {
      const storedLanguageCode = await AsyncStorage.getItem(LANGUAGE_KEY);
      if (storedLanguageCode) {
        const language = LANGUAGES.find(lang => lang.code === storedLanguageCode);
        if (language) {
          setSelectedLanguage(language);
        }
      }
    } catch (error) {
      console.error('Error loading language:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveLanguage = async (language: Language) => {
    try {
      await AsyncStorage.setItem(LANGUAGE_KEY, language.code);
      setSelectedLanguage(language);
      console.log('Language saved:', language.name);
    } catch (error) {
      console.error('Error saving language:', error);
    }
  };

  const clearLanguage = async () => {
    try {
      await AsyncStorage.removeItem(LANGUAGE_KEY);
      setSelectedLanguage(LANGUAGES[0]);
    } catch (error) {
      console.error('Error clearing language:', error);
    }
  };

  return {
    selectedLanguage,
    setSelectedLanguage: saveLanguage,
    clearLanguage,
    isLoading,
    languages: LANGUAGES
  };
}
