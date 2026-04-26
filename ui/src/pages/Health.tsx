import {
  Box,
  Card,
  CardBody,
  Heading,
  SimpleGrid,
  Text,
  VStack,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  Flex,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
} from "@chakra-ui/react"
import { useHealth, useStats, useJobs } from "../hooks/useApi"

export default function Health() {
  const { connected, loading: healthLoading } = useHealth()
  const { stats, loading: statsLoading } = useStats()
  const { jobs } = useJobs(50)

  const pendingJobs = jobs.filter((j) => j.status === "pending").length
  const runningJobs = jobs.filter((j) => j.status === "running").length
  const failedJobs = jobs.filter((j) => j.status === "failed").length

  return (
    <Box>
      <Heading size="lg" mb={6} color="white">
        Health Check
      </Heading>

      {healthLoading ? (
        <Flex justify="center" py={10}>
          <Spinner size="xl" color="brand.500" />
        </Flex>
      ) : connected ? (
        <Alert status="success" mb={6} borderRadius="lg">
          <AlertIcon />
          API Connected — Database healthy
        </Alert>
      ) : (
        <Alert status="error" mb={6} borderRadius="lg">
          <AlertIcon />
          Cannot connect to API
        </Alert>
      )}

      <SimpleGrid columns={{ base: 2, lg: 4 }} spacing={4} mb={6}>
        <Card bg="surface.2" variant="outline" borderColor="surface.3">
          <CardBody>
            <Text fontSize="sm" color="gray.400">API Status</Text>
            <Badge colorScheme={connected ? "green" : "red"} fontSize="md" mt={1}>
              {connected ? "UP" : "DOWN"}
            </Badge>
          </CardBody>
        </Card>
        <Card bg="surface.2" variant="outline" borderColor="surface.3">
          <CardBody>
            <Text fontSize="sm" color="gray.400">Pending Jobs</Text>
            <Text fontSize="2xl" fontWeight="bold" color="yellow.400" mt={1}>
              {pendingJobs}
            </Text>
          </CardBody>
        </Card>
        <Card bg="surface.2" variant="outline" borderColor="surface.3">
          <CardBody>
            <Text fontSize="sm" color="gray.400">Running Jobs</Text>
            <Text fontSize="2xl" fontWeight="bold" color="blue.400" mt={1}>
              {runningJobs}
            </Text>
          </CardBody>
        </Card>
        <Card bg="surface.2" variant="outline" borderColor="surface.3">
          <CardBody>
            <Text fontSize="sm" color="gray.400">Failed Jobs</Text>
            <Text fontSize="2xl" fontWeight="bold" color="red.400" mt={1}>
              {failedJobs}
            </Text>
          </CardBody>
        </Card>
      </SimpleGrid>

      {failedJobs > 0 && (
        <Card bg="surface.2" variant="outline" borderColor="red.500" mb={6}>
          <CardBody>
            <Heading size="sm" color="red.400" mb={3}>
              Failed Jobs
            </Heading>
            <Table variant="simple" size="sm" colorScheme="whiteAlpha">
              <Thead>
                <Tr>
                  <Th color="gray.400">Memory</Th>
                  <Th color="gray.400">Error</Th>
                  <Th color="gray.400">Attempts</Th>
                </Tr>
              </Thead>
              <Tbody>
                {jobs
                  .filter((j) => j.status === "failed")
                  .slice(0, 10)
                  .map((job) => (
                    <Tr key={job.id}>
                      <Td color="gray.300" fontSize="xs" fontFamily="mono">
                        {job.memory_id?.slice(0, 8) || "—"}
                      </Td>
                      <Td color="red.300" fontSize="xs" maxW="400px" isTruncated>
                        {job.last_error || "Unknown"}
                      </Td>
                      <Td color="gray.400" fontSize="xs">
                        {job.attempt_count}
                      </Td>
                    </Tr>
                  ))}
              </Tbody>
            </Table>
          </CardBody>
        </Card>
      )}
    </Box>
  )
}