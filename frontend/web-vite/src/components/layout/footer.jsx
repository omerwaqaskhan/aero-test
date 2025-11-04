import React from 'react';
import { Facebook, Instagram, Linkedin, Mail, Phone } from 'lucide-react';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  const socialLinks = [
    { name: 'Facebook', icon: Facebook, href: '#facebook' },
    { name: 'Instagram', icon: Instagram, href: '#instagram' },
    { name: 'LinkedIn', icon: Linkedin, href: '#linkedin' }
  ];

  return (
    <footer className="bg-gray-800 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12">
          {/* Contact Details */}
          <div className="lg:col-span-1">
            <h4 className="text-lg font-bold mb-4 uppercase">Contact</h4>
            <div className="space-y-3 mb-6">
              <div className="flex items-center text-gray-300">
                <Phone className="w-4 h-4 mr-3 flex-shrink-0" />
                <span className="text-sm">+1 (555) 123-4567</span>
              </div>
              <div className="flex items-center text-gray-300">
                <Phone className="w-4 h-4 mr-3 flex-shrink-0" />
                <span className="text-sm">+1 (555) 987-6543</span>
              </div>
              <div className="flex items-center text-gray-300">
                <Mail className="w-4 h-4 mr-3 flex-shrink-0" />
                <span className="text-sm">support@luftway.com</span>
              </div>
            </div>

            {/* Social Media Icons */}
            <div className="flex space-x-3">
              {socialLinks.map((social) => {
                const Icon = social.icon;
                return (
                  <a
                    key={social.name}
                    href={social.href}
                    className="w-10 h-10 bg-gray-700 hover:bg-orange-600 rounded-full flex items-center justify-center transition-colors duration-300"
                    aria-label={social.name}
                  >
                    <Icon className="w-5 h-5" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Menu */}
          <div className="lg:col-span-1">
            <h4 className="text-lg font-bold mb-4 uppercase">Menu</h4>
            <ul className="space-y-3">
              <li>
                <a href="/" className="text-gray-300 hover:text-white transition-colors duration-200 text-sm">
                  Home
                </a>
              </li>
              <li>
                <a href="#hotels" className="text-gray-300 hover:text-white transition-colors duration-200 text-sm">
                  Hotels
                </a>
              </li>
              <li>
                <a href="#news" className="text-gray-300 hover:text-white transition-colors duration-200 text-sm">
                  News
                </a>
              </li>
              <li>
                <a href="#contacts" className="text-gray-300 hover:text-white transition-colors duration-200 text-sm">
                  Contacts
                </a>
              </li>
            </ul>
          </div>

          {/* Our Partners */}
          <div className="lg:col-span-1">
            <h4 className="text-lg font-bold mb-4 uppercase">Our Partners</h4>
            <ul className="space-y-3">
              <li>
                <a href="#" className="text-gray-300 hover:text-white transition-colors duration-200 text-sm">
                  Hilton
                </a>
              </li>
              <li>
                <a href="#" className="text-gray-300 hover:text-white transition-colors duration-200 text-sm">
                  Marriott
                </a>
              </li>
            </ul>
          </div>

          {/* About Us */}
          <div className="lg:col-span-2">
            <h4 className="text-lg font-bold mb-4 uppercase">LuftWay</h4>
            <p className="text-gray-300 text-sm leading-relaxed mb-4">
              A specialized team of professionals with over 30 years of experience in the hotel and real estate industry. 
              We provide comprehensive services for buying, selling, and managing hotel properties worldwide.
            </p>
            <a href="#about" className="text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors">
              Read more...
            </a>
          </div>
        </div>
      </div>

      {/* Copyright */}
      <div className="border-t border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center">
            <p className="text-gray-400 text-xs">
              &copy; {currentYear} by beanario
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;