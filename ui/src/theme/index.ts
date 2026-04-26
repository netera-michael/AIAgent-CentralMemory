import { extendTheme } from "@chakra-ui/react"

const theme = extendTheme({
  config: {
    initialColorMode: "dark",
    useSystemColorMode: false,
  },
  colors: {
    brand: {
      50: "#eef2ff",
      100: "#dbe4ff",
      200: "#bac8ff",
      300: "#91a7ff",
      400: "#748ffc",
      500: "#5c7cfa",
      600: "#4c6ef5",
      700: "#4263eb",
      800: "#3b5bdb",
      900: "#364fc7",
    },
    surface: {
      0: "#0a0a0f",
      1: "#12121a",
      2: "#1a1a25",
      3: "#22222f",
      4: "#2a2a38",
    },
  },
  styles: {
    global: (props: { colorMode: string }) => ({
      body: {
        bg: props.colorMode === "dark" ? "surface.0" : "gray.50",
        color: props.colorMode === "dark" ? "gray.200" : "gray.800",
      },
    }),
  },
  components: {
    Card: {
      baseStyle: (props: { colorMode: string }) => ({
        container: {
          bg: props.colorMode === "dark" ? "surface.2" : "white",
          boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
          border: props.colorMode === "dark" ? "1px solid" : undefined,
          borderColor: props.colorMode === "dark" ? "surface.4" : undefined,
        },
      }),
    },
  },
})

export default theme