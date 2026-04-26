import { BrowserRouter, Routes, Route } from "react-router-dom"
import { ChakraProvider } from "@chakra-ui/react"
import theme from "./theme"
import Layout from "./components/Layout"
import Dashboard from "./pages/Dashboard"
import Memories from "./pages/Memories"
import Search from "./pages/Search"
import Review from "./pages/Review"
import Entities from "./pages/Entities"
import System from "./pages/System"
import Health from "./pages/Health"

export default function App() {
  return (
    <ChakraProvider theme={theme}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/memories" element={<Memories />} />
            <Route path="/search" element={<Search />} />
            <Route path="/review" element={<Review />} />
            <Route path="/entities" element={<Entities />} />
            <Route path="/system" element={<System />} />
            <Route path="/health" element={<Health />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ChakraProvider>
  )
}