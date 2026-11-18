import { Platform } from "react-native";

export const colors = {
  paper: "#EBE3CF",
  surface: "#F8F3E6",
  ink: "#1E2A22",
  inkSoft: "#46554B",
  muted: "#56665A",
  line: "#D2C7AC",
  primary: "#1F4D3A",
  primaryText: "#F8F3E6",
  accent: "#8F520E",
  accentSoft: "#EFDFBA",
  danger: "#A3321F",
  dangerSoft: "#F1D9CF",
  success: "#2F6B3A",
  successSoft: "#DCE8CF",
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
