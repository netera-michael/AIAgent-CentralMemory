import { Box } from "@chakra-ui/react"
import Sidebar from "./Sidebar"

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <Box minH="100vh" bg="surface.0">
      <Sidebar />
      <Box ml="240px" p={6}>
        {children}
      </Box>
    </Box>
  )
}