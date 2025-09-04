import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import Home from './pages/Home.jsx';
import Contatti from './pages/Contatti.jsx';
import About from './pages/About.jsx';
import Twitter from './pages/Twitter.jsx';
import Instagram from './pages/Instagram.jsx';
import CreateProduct from './pages/CreateProduct.jsx';
import INCI from './pages/INCI.jsx';

import { createBrowserRouter, RouterProvider } from 'react-router-dom';

const router = createBrowserRouter([
  {
    path: "/",
    element: <Home />,
  },
  {
    path: "/about",
    element: <About />,
  },
  {
    path: "/contatti",
    element: <Contatti />,
  },
  {
    path: "/twitter",
    element: <Twitter />,
  },
  {
    path: "/instagram",
    element: <Instagram />,
  },
  {
    path: "/product",
    element: <CreateProduct />,
  },
  {
    path: "/inci",
    element: <INCI />,
  },
]);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
