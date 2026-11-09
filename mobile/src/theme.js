import { Platform } from "react-native";

export const colors = {
  paper: "#F5F1E8",
  surface: "#FFFFFF",
  ink: "#17212B",
  inkSoft: "#4A5663",
  muted: "#7B8590",
  line: "#E2DCCD",
  primary: "#133552",
  primaryText: "#FFFFFF",
  accent: "#B4701B",
  accentSoft: "#F3E6D0",
  danger: "#A3321F",
  dangerSoft: "#F6E1DC",
  success: "#2F6B4F",
};

export const serif = Platform.select({ ios: "Georgia", android: "serif", default: "Georgia, serif" });

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 };

export const type = {
  display: { fontFamily: serif, fontSize: 30, lineHeight: 36, color: colors.ink },
  title: { fontFamily: serif, fontSize: 22, lineHeight: 28, color: colors.ink },
  heading: { fontFamily: serif, fontSize: 18, lineHeight: 24, color: colors.ink },
  body: { fontSize: 15, lineHeight: 22, color: colors.ink },
  small: { fontSize: 13, lineHeight: 18, color: colors.inkSoft },
  label: { fontSize: 11, lineHeight: 14, letterSpacing: 1.2, textTransform: "uppercase", color: colors.muted, fontWeight: "600" },
};

export const radius = { sm: 4, md: 8 };
