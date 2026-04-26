import { useState } from "react"
import {
  Box,
  Heading,
  Card,
  CardBody,
  Text,
  Badge,
  VStack,
  HStack,
  Button,
  Input,
  FormControl,
  FormLabel,
  Textarea,
  SimpleGrid,
  Spinner,
  Flex,
} from "@chakra-ui/react"
import { useEntities } from "../hooks/useApi"
import * as api from "../api/client"

const ENTITY_TYPES = ["person", "project", "server", "device", "service", "company"]

export default function Entities() {
  const { entities, loading, refetch } = useEntities()
  const [name, setName] = useState("")
  const [type, setType] = useState("person")
  const [desc, setDesc] = useState("")
  const [creating, setCreating] = useState(false)

  const handleCreate = async () => {
    if (!name.trim()) return
    setCreating(true)
    try {
      await api.createEntity({
        name: name.trim(),
        type,
        description: desc.trim() || undefined,
      })
      setName("")
      setDesc("")
      refetch()
    } catch (e) {
      alert(`Failed: ${e}`)
    } finally {
      setCreating(false)
    }
  }

  const typeCounts = entities.reduce<Record<string, number>>((acc, e) => {
    acc[e.type] = (acc[e.type] || 0) + 1
    return acc
  }, {})

  if (loading)
    return (
      <Flex justify="center" pt={20}>
        <Spinner size="xl" color="brand.500" />
      </Flex>
    )

  return (
    <Box>
      <Heading size="lg" mb={6} color="white">
        Entities
      </Heading>

      <Card bg="surface.2" variant="outline" borderColor="surface.3" mb={6}>
        <CardBody>
          <Heading size="sm" mb={4} color="white">
            Create Entity
          </Heading>
          <SimpleGrid columns={3} spacing={4}>
            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">
                Name
              </FormLabel>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Contabo VPS"
                bg="surface.4"
                color="white"
                border="1px solid"
                borderColor="surface.4"
              />
            </FormControl>
            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">
                Type
              </FormLabel>
              <HStack>
                {ENTITY_TYPES.map((t) => (
                  <Button
                    key={t}
                    size="sm"
                    variant={type === t ? "solid" : "outline"}
                    colorScheme={type === t ? "brand" : "gray"}
                    onClick={() => setType(t)}
                  >
                    {t}
                  </Button>
                ))}
              </HStack>
            </FormControl>
            <FormControl>
              <FormLabel color="gray.400" fontSize="sm">
                Description (optional)
              </FormLabel>
              <Input
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                placeholder="Brief description"
                bg="surface.4"
                color="white"
                border="1px solid"
                borderColor="surface.4"
              />
            </FormControl>
          </SimpleGrid>
          <Button
            mt={4}
            colorScheme="brand"
            onClick={handleCreate}
            isLoading={creating}
            isDisabled={!name.trim()}
          >
            Create Entity
          </Button>
        </CardBody>
      </Card>

      <SimpleGrid columns={{ base: 2, lg: 4 }} spacing={3} mb={4}>
        {Object.entries(typeCounts).map(([t, count]) => (
          <Card key={t} bg="surface.2" variant="outline" borderColor="surface.3">
            <CardBody py={2}>
              <Text fontSize="sm" color="gray.400">
                {t}
              </Text>
              <Text fontSize="xl" fontWeight="bold" color="white">
                {count}
              </Text>
            </CardBody>
          </Card>
        ))}
      </SimpleGrid>

      <VStack spacing={2} align="stretch">
        {entities.map((entity) => (
          <Card
            key={entity.id}
            bg="surface.2"
            variant="outline"
            borderColor="surface.3"
            _hover={{ borderColor: "brand.500" }}
          >
            <CardBody py={3}>
              <Flex justify="space-between" align="center">
                <Box>
                  <HStack spacing={2}>
                    <Text fontWeight="semibold" color="white" fontSize="sm">
                      {entity.name}
                    </Text>
                    <Badge colorScheme="purple" fontSize="2xs">
                      {entity.type}
                    </Badge>
                  </HStack>
                  {entity.description && (
                    <Text fontSize="xs" color="gray.400" mt={1}>
                      {entity.description}
                    </Text>
                  )}
                </Box>
                <Text fontSize="2xs" color="gray.600" fontFamily="mono">
                  {entity.id.slice(0, 8)}
                </Text>
              </Flex>
            </CardBody>
          </Card>
        ))}
      </VStack>
    </Box>
  )
}