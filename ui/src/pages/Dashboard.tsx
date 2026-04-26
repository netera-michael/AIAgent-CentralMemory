import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Card,
  CardBody,
  Heading,
  Text,
  Flex,
  Badge,
  Spinner,
  Alert,
  AlertIcon,
  VStack,
  HStack,
  Progress,
} from "@chakra-ui/react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts"
import { useStats, useMemories, useReviewItems, useJobs } from "../hooks/useApi"

const SCOPE_COLORS: Record<string, string> = {
  personal: "#3fb950",
  personal_finance: "#d29922",
  biz_finance: "#f85149",
  biz_projects: "#bc8cff",
  coding_projects: "#58a6ff",
  infrastructure: "#79c0ff",
  social_media_clients: "#ff9bce",
}

const STATUS_COLORS: Record<string, string> = {
  canonical: "#58a6ff",
  reviewed: "#3fb950",
  scratch: "#d29922",
  stale: "#8b949e",
  conflicted: "#f85149",
  archived: "#6e7681",
}

export default function Dashboard() {
  const { stats, loading: statsLoading, error: statsError } = useStats()
  const { memories, loading: memLoading } = useMemories(true)
  const { items: reviewItems } = useReviewItems()
  const { jobs } = useJobs()

  if (statsLoading || memLoading)
    return (
      <Flex justify="center" pt={20}>
        <Spinner size="xl" color="brand.500" />
      </Flex>
    )

  if (statsError)
    return (
      <Alert status="error">
        <AlertIcon />
        {statsError}
      </Alert>
    )

  const byStatus = stats?.by_status || {}
  const byScope = stats?.by_scope || {}
  const byType = stats?.by_type || {}
  const total = stats?.total || 0
  const pendingReviews = stats?.pending_reviews || 0
  const failedJobs = jobs.filter((j) => j.status === "failed").length

  const timelineData = (() => {
    const dayCounts: Record<string, number> = {}
    memories.forEach((m) => {
      const day = m.created_at?.slice(0, 10)
      if (day) dayCounts[day] = (dayCounts[day] || 0) + 1
    })
    return Object.entries(dayCounts)
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-30)
      .map(([date, count]) => ({ date: date.slice(5), count }))
  })()

  const scopeData = Object.entries(byScope).map(([name, value]) => ({
    name,
    value,
    color: SCOPE_COLORS[name] || "#8b949e",
  }))

  const typeData = Object.entries(byType)
    .sort(([, a], [, b]) => b - a)
    .map(([name, value]) => ({ name, value }))

  return (
    <Box>
      <Heading size="lg" mb={6} color="white">
        Dashboard
      </Heading>

      <SimpleGrid columns={{ base: 2, lg: 5 }} spacing={4} mb={6}>
        <Card bg="navy.700" variant="outline" borderColor="whiteAlpha.100">
          <CardBody>
            <Stat>
              <StatLabel color="gray.400">Total</StatLabel>
              <StatNumber color="white">{total}</StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card bg="navy.700" variant="outline" borderColor="whiteAlpha.100">
          <CardBody>
            <Stat>
              <StatLabel color="gray.400">Canonical</StatLabel>
              <StatNumber color="blue.400">{byStatus.canonical || 0}</StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card bg="navy.700" variant="outline" borderColor="whiteAlpha.100">
          <CardBody>
            <Stat>
              <StatLabel color="gray.400">Reviewed</StatLabel>
              <StatNumber color="green.400">{byStatus.reviewed || 0}</StatNumber>
            </Stat>
          </CardBody>
        </Card>
        <Card bg="navy.700" variant="outline" borderColor="whiteAlpha.100">
          <CardBody>
            <Stat>
              <StatLabel color="gray.400">Scratch</StatLabel>
              <StatNumber color="yellow.400">{byStatus.scratch || 0}</StatNumber>
              {byStatus.scratch > 0 && (
                <StatHelpText color="yellow.300">Needs review</StatHelpText>
              )}
            </Stat>
          </CardBody>
        </Card>
        <Card bg="navy.700" variant="outline" borderColor="whiteAlpha.100">
          <CardBody>
            <Stat>
              <StatLabel color="gray.400">Pending Reviews</StatLabel>
              <StatNumber color="orange.400">{pendingReviews}</StatNumber>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {failedJobs > 0 && (
        <Alert status="error" mb={4} borderRadius="lg">
          <AlertIcon />
          {failedJobs} failed ingestion job(s) need attention
        </Alert>
      )}

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4} mb={6}>
        <Card bg="navy.700" variant="outline" borderColor="whiteAlpha.100">
          <CardBody>
            <Heading size="sm" mb={4} color="white">
              Memory Timeline
            </Heading>
            {timelineData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={timelineData}>
                  <XAxis dataKey="date" stroke="#8b949e" fontSize={11} />
                  <YAxis stroke="#8b949e" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      background: "#1a202c",
                      border: "1px solid #4a5568",
                      borderRadius: 8,
                    }}
                  />
                  <Bar dataKey="count" fill="#4c6ef5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Text color="gray.500">No timeline data</Text>
            )}
          </CardBody>
        </Card>

        <Card bg="navy.700" variant="outline" borderColor="whiteAlpha.100">
          <CardBody>
            <Heading size="sm" mb={4} color="white">
              By Scope
            </Heading>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={scopeData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, percent }: { name?: string; percent?: number }) =>
                    `${name || ""} ${((percent || 0) * 100).toFixed(0)}%`
                  }
                >
                  {scopeData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={4}>
        <Card bg="navy.700" variant="outline" borderColor="whiteAlpha.100">
          <CardBody>
            <Heading size="sm" mb={4} color="white">
              By Type
            </Heading>
            <VStack spacing={3} align="stretch">
              {typeData.map(({ name, value }) => (
                <Box key={name}>
                  <Flex justify="space-between" mb={1}>
                    <Text fontSize="sm" color="gray.300">
                      {name}
                    </Text>
                    <Text fontSize="sm" color="gray.400">
                      {value} ({((value / total) * 100).toFixed(0)}%)
                    </Text>
                  </Flex>
                  <Progress
                    value={(value / total) * 100}
                    size="sm"
                    colorScheme="brand"
                    borderRadius="full"
                    bg="whiteAlpha.100"
                  />
                </Box>
              ))}
            </VStack>
          </CardBody>
        </Card>

        <Card bg="navy.700" variant="outline" borderColor="whiteAlpha.100">
          <CardBody>
            <Heading size="sm" mb={4} color="white">
              By Status
            </Heading>
            <VStack spacing={3} align="stretch">
              {Object.entries(byStatus)
                .sort(([, a], [, b]) => b - a)
                .map(([status, count]) => (
                  <Box key={status}>
                    <Flex justify="space-between" mb={1}>
                      <HStack spacing={2}>
                        <Badge
                          colorScheme={
                            status === "canonical"
                              ? "blue"
                              : status === "reviewed"
                                ? "green"
                                : status === "scratch"
                                  ? "yellow"
                                  : status === "archived"
                                    ? "gray"
                                    : "red"
                          }
                        >
                          {status}
                        </Badge>
                      </HStack>
                      <Text fontSize="sm" color="gray.400">
                        {count}
                      </Text>
                    </Flex>
                    <Box
                      h={2}
                      borderRadius="full"
                      bg={STATUS_COLORS[status] || "#8b949e"}
                      w={`${(count / total) * 100}%`}
                      opacity={0.8}
                    />
                  </Box>
                ))}
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>
    </Box>
  )
}