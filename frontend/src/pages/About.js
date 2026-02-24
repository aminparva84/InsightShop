import React from 'react';
import { Link } from 'react-router-dom';
import './InfoPages.css';
import './About.css';

const About = () => {
  return (
    <div className="info-page about-page">
      <header className="info-page-hero">
        <h1>Our Story</h1>
        <p>We believe in clothing that lasts—thoughtfully designed, responsibly made, and made for you.</p>
      </header>

      <div className="info-page-content">
        <section className="info-section">
          <h2>Who We Are</h2>
          <p>
            InsightShop was born from a simple idea: fashion should feel good in every sense. We curate
            timeless pieces that blend quality craftsmanship with modern style, so you can build a
            wardrobe you love—without the clutter or the compromise.
          </p>
          <p>
            Whether you're dressing for the office, the weekend, or a special occasion, we're here to
            help you find pieces that fit your life and your values.
          </p>
        </section>

        <section className="info-section">
          <h2>Mission & Values</h2>
          <ul>
            <li><strong>Quality first</strong> — We source and design with durability and comfort in mind.</li>
            <li><strong>Transparency</strong> — We're honest about our materials, processes, and partners.</li>
            <li><strong>Customer focus</strong> — Your experience and satisfaction guide every decision we make.</li>
            <li><strong>Timeless style</strong> — We favor enduring design over fleeting trends.</li>
          </ul>
        </section>

        <section className="info-section">
          <h2>Quality & Sustainability</h2>
          <p>
            We're committed to reducing our footprint without sacrificing style. From choosing
            more sustainable fabrics to working with suppliers who share our standards, we take
            small, concrete steps toward a more responsible fashion industry.
          </p>
          <p>
            We believe in buying less and wearing more—pieces you'll reach for again and again,
            season after season.
          </p>
        </section>

        <section className="info-section">
          <h2>Why Choose Us</h2>
          <ul>
            <li>Curated selection of modern, versatile clothing</li>
            <li>Clear sizing, honest descriptions, and easy returns</li>
            <li>Friendly, responsive customer support</li>
            <li>Secure checkout and reliable shipping</li>
          </ul>
        </section>

        <section className="info-section">
          <h2>Our Vision</h2>
          <p>
            We want to be the place you think of when you need something you'll actually wear—where
            style meets substance and every purchase feels like a good decision. Thank you for being
            part of our story.
          </p>
        </section>

        <div className="info-cta-block">
          <p>Discover pieces that fit your style and your life.</p>
          <Link to="/products" className="btn btn-primary">Explore Our Collection</Link>
        </div>
      </div>
    </div>
  );
};

export default About;
