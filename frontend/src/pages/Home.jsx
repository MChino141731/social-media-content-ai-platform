// src/pages/Home.jsx
import CardItem from "../components/CardItem";
import { Link } from "react-router-dom";

function Home() {
  const features = [
    {
      title: "Twitter",
      path: "/twitter",
      description: "Generate a post for Twitter with trending hashtags",
      imgURL: "https://cdn-icons-png.flaticon.com/512/733/733579.png",
    },
    {
      title: "Instagram",
      path: "/instagram",
      description: "Generate a post for Instagram with image",
      imgURL: "https://cdn-icons-png.flaticon.com/512/2111/2111463.png",
    },
    {
      title: "New Product",
      path: "/product",
      description: "Generate a sustainable product",
      imgURL: "https://img.freepik.com/premium-photo/cosmetic-skin-care-products-body-lotion-hair-shampoo-face-creme-green-leaves-as-background-top-view-copy-space-natural-eco-beauty-organic-green-skin-care-concept_1028938-390839.jpg",
    },
    {
      title: "Check INCI",
      path: "/inci",
      description: "Check cosmetic ingredients and add to the green/red list",
      imgURL: "https://manunatu.pl/wp-content/uploads/2022/12/sklad-kosmetykow-inci-scaled.jpg",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-start bg-gray-50 text-gray-900">
      <header className="w-full max-w-6xl p-8 text-center">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          Social Media Content AI Platform
        </h1>
        <p className="text-lg md:text-xl text-gray-800">
          Powering the Voices of Sustainability in the Digital Age
        </p>
      </header>

      <main className="w-full max-w-6xl p-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((f) => (
            <Link key={f.title} to={f.path} className="transform hover:scale-105 transition-transform">
              <CardItem title={f.title} imgURL={f.imgURL}>
                {f.description}
              </CardItem>
            </Link>
          ))}
        </div>
      </main>

            <footer className="mt-16 border-t border-gray-300 pt-6 text-center w-full bg-gray-50">
        <Link 
            to="/about" 
            className="text-gray-600 hover:text-blue-600 mx-4 font-medium transition-colors"
        >
            About us
        </Link>
        <Link 
            to="/contatti" 
            className="text-gray-600 hover:text-blue-600 mx-4 font-medium transition-colors"
        >
            Contact
        </Link>
        </footer>

    </div>
  );
}

export default Home;
