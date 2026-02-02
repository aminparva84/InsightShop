import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { CartProvider } from './contexts/CartContext';
import { NotificationProvider } from './contexts/NotificationContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import FloatingAIAssistant from './components/FloatingAIAssistant';
import Home from './pages/Home';
import Products from './pages/Products';
import ProductDetail from './pages/ProductDetail';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import Login from './pages/Login';
import Register from './pages/Register';
import Activation from './pages/Activation';
import Members from './pages/Members';
import OrderConfirmation from './pages/OrderConfirmation';
import Compare from './pages/Compare';
import Admin from './pages/Admin';
import './App.css';

function AppContent() {
  const location = useLocation();
  const isAdmin = location.pathname === '/admin';
  return (
    <div className="App">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:id" element={<ProductDetail />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/activation" element={<Activation />} />
          <Route path="/members" element={<Members />} />
          <Route path="/order-confirmation" element={<OrderConfirmation />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>
      {!isAdmin && <Footer />}
      <FloatingAIAssistant />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <NotificationProvider>
          <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <AppContent />
          </Router>
        </NotificationProvider>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;

