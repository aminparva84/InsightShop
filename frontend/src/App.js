import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { CartProvider } from './contexts/CartContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { WishlistProvider } from './contexts/WishlistContext';
import { AdminNavSyncProvider } from './contexts/AdminNavSyncContext';
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
import Wishlist from './pages/Wishlist';
import About from './pages/About';
import Contact from './pages/Contact';
import ShippingInfo from './pages/ShippingInfo';
import Returns from './pages/Returns';
import Admin from './pages/Admin';
import RequireAuth from './components/RequireAuth';
import './App.css';

/** Scroll window to top on every route change so each page starts at the top. */
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

function AppContent() {
  const location = useLocation();
  const isAdmin = location.pathname === '/admin';
  return (
    <div className="App">
      <ScrollToTop />
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
          <Route path="/members" element={<RequireAuth path="/members"><Members /></RequireAuth>} />
          <Route path="/wishlist" element={<RequireAuth path="/wishlist"><Wishlist /></RequireAuth>} />
          <Route path="/order-confirmation" element={<OrderConfirmation />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/shipping" element={<ShippingInfo />} />
          <Route path="/returns" element={<Returns />} />
          <Route path="/admin" element={<RequireAuth path="/admin" requireSuperadmin><Admin /></RequireAuth>} />
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
          <WishlistProvider>
          <AdminNavSyncProvider>
          <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <AppContent />
          </Router>
          </AdminNavSyncProvider>
          </WishlistProvider>
        </NotificationProvider>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;

