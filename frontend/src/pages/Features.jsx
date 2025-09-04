// src/pages/Features.jsx
import Navbar from "../components/Navbar";
import CardItem from "../components/CardItem";
import { Link } from "react-router-dom";

function Features() {
  const features = [
    { title: "Crea Post Twitter", path: "/twitter", imgURL: "https://cdn-icons-png.flaticon.com/512/733/733579.png", description: "Genera un post per Twitter" },
    { title: "Crea Post Instagram", path: "/instagram", imgURL: "https://cdn-icons-png.flaticon.com/512/2111/2111463.png", description: "Genera un post per Instagram" },
    { title: "Crea Prodotto", path: "/create-product", imgURL: "https://cdn-icons-png.flaticon.com/512/684/684908.png", description: "Genera un prodotto sostenibile" },
    { title: "Check INCI", path: "/inci", imgURL: "https://cdn-icons-png.flaticon.com/512/616/616408.png", description: "Controlla ingredienti cosmetici" },
  ];

  return (
    <>
      <Navbar />
      <h1 className="text-3xl font-bold mb-10 text-center">Seleziona un’operazione</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {features.map((f) => (
          <Link key={f.title} to={f.path}>
            <CardItem title={f.title} imgURL={f.imgURL}>
              {f.description}
            </CardItem>
          </Link>
        ))}
      </div>
    </>
  );
}

export default Features;
