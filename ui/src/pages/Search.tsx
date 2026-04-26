import { useState } from "react"
import {
  Box,
  Heading,
  Input,
  Select,
  HStack,
  Card,
  CardBody,
  Text,
  Badge,
  VStack,
  Button,
  Spinner,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  FormControl,
  FormLabel,
  Switch,
  Flex,
} from "@chakra-ui/react"
import { FiSearch } from "react-icons/fi"
import * as api from "../api/client"
import type { Memory } from "../api/client"

const SCOPES = [
  "personal",
  "personal_finance",
  "biz_finance",
  "biz_projects",
  "coding_projects",
  "infrastructure",
  "social_media_clients",
]

const STATUS_COLORS: Record<string, string> = {
  canonical: "blue",
  reviewed: "green",
  scratch: "yellow",
  stale: "gray",
  conflicted: "red",
  archived: "gray",
}

export default function Search() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<Memory[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [includeScratch, setIncludeScratch] = useState(false)
  const [includeInvalidated, setIncludeInvalidated] = useState(false)
  const [limit, setLimit] = useState(10)
  const [threshold, setThreshold] = useState(2.0)
  const [scopeFilter, setScopeFilter] = useState<string>("")
  const [typeFilter, setTypeFilter] = useState<string>("")

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.semanticSearch({
        query: query.trim(),
        include_scratch: includeScratch,
        include_invalidated: includeInvalidated,
        limit,
        threshold,
        scopes: scopeFilter ? [scopeFilter] : undefined,
        type: typeFilter || undefined,
      })
      setResults(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Search failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Heading size="lg" mb={6} color="white">
        Semantic Search
      </Heading>

      <Card bg="navy.700" variant="outline" borderColor="whiteAlpha.100" mb={6}>
        <CardBody>
          <HStack spacing={3} mb={4}>
            <Input
              placeholder="Search by meaning..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              size="lg"
              bg="navy.900"
              color="white"
              border="1px solid"
              borderColor="whiteAlpha.200"
              _placeholder={{ color: "gray.500" }}
            />
            <Button
              leftIcon={<FiSearch />}
              colorScheme="brand"
              onClick={handleSearch}
              isLoading={loading}
              size="lg"
              px={8}
            >
              Search
            </Button>
          </HStack>

          <HStack spacing={4} flexWrap="wrap">
            <FormControl display="flex" alignItems="center">
              <Switch
                id="scratch"
                isChecked={includeScratch}
                onChange={(e) => setIncludeScratch(e.target.checked)}
                colorScheme="yellow"
                mr={2}
              />
              <FormLabel htmlFor="scratch" mb={0} fontSize="sm" color="gray.400">
                Include Scratch
              </FormLabel>
            </FormControl>
            <FormControl display="flex" alignItems="center">
              <Switch
                id="invalidated"
                isChecked={includeInvalidated}
                onChange={(e) => setIncludeInvalidated(e.target.checked)}
                colorScheme="orange"
                mr={2}
              />
              <FormLabel htmlFor="invalidated" mb={0} fontSize="sm" color="gray.400">
                Include Invalidated
              </FormLabel>
            </FormControl>
            <Select
              placeholder="Scope"
              value={scopeFilter}
              onChange={(e) => setScopeFilter(e.target.value)}
              maxW="180px"
              bg="navy.900"
              color="white"
              border="1px solid"
              borderColor="whiteAlpha.200"
              size="sm"
            >
              {SCOPES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </Select>
            <Select
              placeholder="Type"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              maxW="150px"
              bg="navy.900"
              color="white"
              border="1px solid"
              borderColor="whiteAlpha.200"
              size="sm"
            >
              <option value="fact">fact</option>
              <option value="preference">preference</option>
              <option value="decision">decision</option>
              <option value="workflow">workflow</option>
              <option value="project_note">project_note</option>
            </Select>
            <FormControl maxW="100px">
              <FormLabel fontSize="xs" color="gray.400" mb={0}>
                Limit
              </FormLabel>
              <NumberInput
                value={limit}
                onChange={(_, v) => setLimit(v)}
                min={1}
                max={50}
                size="sm"
              >
                <NumberInputField bg="navy.900" color="white" />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
            </FormControl>
            <FormControl maxW="120px">
              <FormLabel fontSize="xs" color="gray.400" mb={0}>
                Threshold
              </FormLabel>
              <NumberInput
                value={threshold}
                onChange={(_, v) => setThreshold(v)}
                min={0}
                max={2}
                step={0.1}
                size="sm"
              >
                <NumberInputField bg="navy.900" color="white" />
              </NumberInput>
            </FormControl>
          </HStack>
        </CardBody>
      </Card>

      {error && (
        <Text color="red.400" mb={4}>
          {error}
        </Text>
      )}

      {loading && (
        <Flex justify="center" py={10}>
          <Spinner size="xl" color="brand.500" />
        </Flex>
      )}

      {!loading && results.length > 0 && (
        <Box>
          <Text color="gray.400" mb={4} fontSize="sm">
            {results.length} result{results.length !== 1 ? "s" : ""}
          </Text>
          <VStack spacing={3} align="stretch">
            {results.map((mem, i) => (
              <Card
                key={mem.id}
                bg="navy.700"
                variant="outline"
                borderColor="whiteAlpha.100"
                _hover={{ borderColor: "brand.500" }}
                cursor="pointer"
                transition="all 0.15s"
              >
                <CardBody>
                  <Flex justify="space-between" align="start" mb={2}>
                    <Box>
                      <HStack spacing={2} mb={1}>
                        <Text color="gray.500" fontSize="xs">
                          #{i + 1}
                        </Text>
                        <Badge colorScheme={STATUS_COLORS[mem.status] || "gray"}>
                          {mem.status}
                        </Badge>
                        <Badge colorScheme="purple">{mem.type}</Badge>
                        <Badge colorScheme="cyan">{mem.scope}</Badge>
                        {mem.valid_from && !mem.valid_until && (
                          <Badge colorScheme="green">active</Badge>
                        )}
                        {mem.valid_until && (
                          <Badge colorScheme="red">invalidated</Badge>
                        )}
                      </HStack>
                      <Text fontWeight="semibold" color="white" fontSize="md">
                        {mem.title || mem.id.slice(0, 8)}
                      </Text>
                    </Box>
                    <Text fontSize="xs" color="gray.500">
                      {mem.created_at?.slice(0, 10)}
                    </Text>
                  </Flex>
                  {mem.summary && (
                    <Text fontSize="sm" color="gray.300" mb={2}>
                      {mem.summary}
                    </Text>
                  )}
                  <Text fontSize="sm" color="gray.400" noOfLines={3}>
                    {mem.content}
                  </Text>
                </CardBody>
              </Card>
            ))}
          </VStack>
        </Box>
      )}

      {!loading && query && results.length === 0 && !error && (
        <Text color="gray.500" textAlign="center" py={10}>
          No results found. Try lowering the threshold or adjusting filters.
        </Text>
      )}
    </Box>
  )
}