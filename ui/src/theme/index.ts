import { extendTheme } from "@chakra-ui/react"

const theme = extendTheme({
  config: {
    initialColorMode: "dark",
    useSystemColorMode: false,
  },
  colors: {
    brand: {
      50: "#e6f2ff",
      100: "#b3d9ff",
      200: "#80bfff",
      300: "#4da6ff",
      400: "#1a8cff",
      500: "#0072ff",
      600: "#0059cc",
      700: "#004099",
      800: "#002666",
      900: "#000d33",
    },
    navy: {
      50: "#d0dcfb",
      100: "#aac0fe",
      200: "#a3b9f8",
      300: "#728feb",
      400: "#5e81f4",
      500: "#4c6ef5",
      600: "#3b4db8",
      700: "#2c3682",
      800: "#1e2458",
      900: "#111c44",
    },
  },
  styles: {
    global: (props: { colorMode: string }) => ({
      body: {
        bg: props.colorMode === "dark" ? "#111c44" : "gray.50",
        color: props.colorMode === "dark" ? "whiteAlpha.900" : "gray.800",
      },
    }),
  },
  components: {
    Card: {
      baseStyle: (props: { colorMode: string }) => ({
        container: {
          bg: props.colorMode === "dark" ? "navy.700" : "white",
          boxShadow: "0px 5px 14px rgba(0,0,0,0.05)",
        },
      }),
    },
  },
})

export default theme