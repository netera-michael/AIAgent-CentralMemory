import { Box } from "@chakra-ui/react"
import Sidebar from "./Sidebar"

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <Box minH="100vh" bg="navy.900">
      <Sidebar />
      <Box ml="260px" p={8}>
        {children}
      </Box>
    </Box>
  )
}