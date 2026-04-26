import { Box, Flex, Icon, Text, VStack, Link, Spacer, Badge } from "@chakra-ui/react"
import {
  FiHome,
  FiDatabase,
  FiSearch,
  FiCheckSquare,
  FiGrid,
  FiSettings,
  FiActivity,
} from "react-icons/fi"
import { useHealth } from "../hooks/useApi"
import { Link as RouterLink, useLocation } from "react-router-dom"

const NAV_ITEMS = [
  { label: "Dashboard", icon: FiHome, path: "/" },
  { label: "Memories", icon: FiDatabase, path: "/memories" },
  { label: "Search", icon: FiSearch, path: "/search" },
  { label: "Review", icon: FiCheckSquare, path: "/review" },
  { label: "Entities", icon: FiGrid, path: "/entities" },
  { label: "System", icon: FiSettings, path: "/system" },
  { label: "Health", icon: FiActivity, path: "/health" },
]

export default function Sidebar() {
  const location = useLocation()
  const { connected } = useHealth()

  return (
    <Box
      w="240px"
      h="100vh"
      bg="surface.1"
      borderRight="1px solid"
      borderRightColor="surface.3"
      position="fixed"
      left={0}
      top={0}
      overflowY="auto"
    >
      <Flex direction="column" h="full">
        <Box p={5} pb={3}>
          <Text fontSize="lg" fontWeight="bold" color="white" letterSpacing="tight">
            CentralMemory
          </Text>
          <Text fontSize="xs" color="gray.500" mt={0.5}>
            Memory Control Panel
          </Text>
        </Box>

        <VStack spacing={0.5} align="stretch" px={3} flex={1}>
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <Link
                as={RouterLink}
                key={item.path}
                to={item.path}
                display="flex"
                alignItems="center"
                px={3}
                py={2}
                borderRadius="md"
                bg={isActive ? "brand.600" : "transparent"}
                color={isActive ? "white" : "gray.400"}
                _hover={{ bg: isActive ? "brand.600" : "surface.3", color: "white" }}
                transition="all 0.1s"
                fontWeight={isActive ? "semibold" : "medium"}
                fontSize="sm"
              >
                <Icon as={item.icon} mr={3} boxSize={4} />
                {item.label}
              </Link>
            )
          })}
        </VStack>

        <Spacer />

        <Box p={4} borderTop="1px solid" borderColor="surface.3">
          <Flex align="center">
            <Box
              w={2}
              h={2}
              borderRadius="full"
              bg={connected ? "green.400" : "red.400"}
              mr={2}
            />
            <Text fontSize="xs" color="gray.500">
              API {connected ? "Connected" : "Disconnected"}
            </Text>
          </Flex>
        </Box>
      </Flex>
    </Box>
  )
}