import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { DefaultTheme, NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useAuth } from "../auth/AuthContext";
import { Loading } from "../components";
import ComposeNoticeScreen from "../screens/ComposeNoticeScreen";
import FacilitiesScreen from "../screens/FacilitiesScreen";
import ForgotPasswordScreen from "../screens/ForgotPasswordScreen";
import HomeScreen from "../screens/HomeScreen";
import LoginScreen from "../screens/LoginScreen";
import MoreScreen from "../screens/MoreScreen";
import NoticesScreen from "../screens/NoticesScreen";
import ProfileScreen from "../screens/ProfileScreen";
import RegisterScreen from "../screens/RegisterScreen";
import ResultsScreen from "../screens/ResultsScreen";
import TimetableScreen from "../screens/TimetableScreen";
import UnitDetailScreen from "../screens/UnitDetailScreen";
import UnitsScreen from "../screens/UnitsScreen";
import VerifyScreen from "../screens/VerifyScreen";
import { colors, serif } from "../theme";

const navTheme = {
  ...DefaultTheme,
  colors: { ...DefaultTheme.colors, background: colors.paper, card: colors.paper, text: colors.ink, primary: colors.primary, border: colors.line },
};

const headerOptions = {
  headerStyle: { backgroundColor: colors.paper },
  headerShadowVisible: false,
  headerTintColor: colors.primary,
  headerTitleStyle: { fontFamily: serif, color: colors.ink, fontSize: 18 },
  headerBackButtonDisplayMode: "minimal",
  contentStyle: { backgroundColor: colors.paper },
};

const AuthStack = createNativeStackNavigator();
const AppStack = createNativeStackNavigator();
const Tabs = createBottomTabNavigator();

function TabBar({ state, descriptors, navigation }) {
  const insets = useSafeAreaInsets();
  return (
    <View style={[styles.bar, { paddingBottom: Math.max(insets.bottom, 8) }]}>
      {state.routes.map((route, index) => {
        const focused = state.index === index;
        const label = descriptors[route.key].options.title || route.name;
        const press = () => {
          const event = navigation.emit({ type: "tabPress", target: route.key, canPreventDefault: true });
          if (!focused && !event.defaultPrevented) navigation.navigate(route.name);
        };
        return (
          <Pressable key={route.key} onPress={press} accessibilityRole="tab" accessibilityState={{ selected: focused }} accessibilityLabel={label} style={styles.tab}>
            <View style={[styles.indicator, focused && styles.indicatorOn]} />
            <Text style={[styles.tabText, focused && styles.tabTextOn]}>{label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

function MainTabs() {
  return (
    <Tabs.Navigator tabBar={(props) => <TabBar {...props} />} screenOptions={{ headerShown: false }}>
      <Tabs.Screen name="Home" component={HomeScreen} options={{ title: "Home" }} />
      <Tabs.Screen name="Timetable" component={TimetableScreen} options={{ title: "Timetable" }} />
      <Tabs.Screen name="Units" component={UnitsScreen} options={{ title: "Units" }} />
      <Tabs.Screen name="Notices" component={NoticesScreen} options={{ title: "Notices" }} />
      <Tabs.Screen name="More" component={MoreScreen} options={{ title: "More" }} />
    </Tabs.Navigator>
  );
}

export default function Navigation() {
  const { status } = useAuth();
  if (status === "loading") return <Loading />;

  return (
    <NavigationContainer theme={navTheme}>
      {status === "signedIn" ? (
        <AppStack.Navigator screenOptions={headerOptions}>
          <AppStack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
          <AppStack.Screen name="UnitDetail" component={UnitDetailScreen} options={{ title: "Unit" }} />
          <AppStack.Screen name="Results" component={ResultsScreen} options={{ title: "Results" }} />
          <AppStack.Screen name="Facilities" component={FacilitiesScreen} options={{ title: "Campus directory" }} />
          <AppStack.Screen name="Profile" component={ProfileScreen} options={{ title: "Profile" }} />
          <AppStack.Screen name="ComposeNotice" component={ComposeNoticeScreen} options={{ title: "New notice" }} />
        </AppStack.Navigator>
      ) : (
        <AuthStack.Navigator screenOptions={headerOptions}>
          <AuthStack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
          <AuthStack.Screen name="Register" component={RegisterScreen} options={{ title: "" }} />
          <AuthStack.Screen name="Verify" component={VerifyScreen} options={{ title: "" }} />
          <AuthStack.Screen name="ForgotPassword" component={ForgotPasswordScreen} options={{ title: "" }} />
        </AuthStack.Navigator>
      )}
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  bar: { flexDirection: "row", backgroundColor: colors.surface, borderTopWidth: 1, borderTopColor: colors.line },
  tab: { flex: 1, alignItems: "center", paddingBottom: 6 },
  indicator: { height: 3, width: 24, borderRadius: 2, backgroundColor: "transparent", marginBottom: 10 },
  indicatorOn: { backgroundColor: colors.accent },
  tabText: { fontSize: 12, fontWeight: "500", color: colors.muted, letterSpacing: 0.2 },
  tabTextOn: { color: colors.ink, fontWeight: "700" },
});
