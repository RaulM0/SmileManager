module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  corePlugins: { preflight: false },
  prefix: "co-",
  theme: {
    extend: {
      colors: {
        clinical: {
          canvas: "#f4f6f7",
          surface: "#ffffff",
          line: "#dce3e6",
          ink: "#1d2a32",
          muted: "#52616a",
          brand: "#176b78",
          brandHover: "#105763",
          tint: "#e8f3f4",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
