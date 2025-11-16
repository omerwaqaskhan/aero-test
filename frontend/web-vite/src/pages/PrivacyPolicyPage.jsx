import { useEffect } from 'react';

export default function PrivacyPolicyPage() {
  useEffect(() => {
    document.title = 'Privacy Policy - Aero Hotels';
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-sm p-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Privacy Policy</h1>
        
        <div className="prose prose-lg max-w-none">
          <p className="text-gray-600 mb-6">
            <strong>Last Updated:</strong> {new Date().toLocaleDateString()}
          </p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Introduction</h2>
            <p className="text-gray-700 mb-4">
              At Aero Hotels, we are committed to protecting your privacy and ensuring the security of your personal information. 
              This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our website 
              and services.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Information We Collect</h2>
            <h3 className="text-xl font-semibold text-gray-800 mb-3">2.1 Personal Information</h3>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>Name, email address, and contact information</li>
              <li>Payment and billing information</li>
              <li>Booking history and preferences</li>
              <li>Account credentials and authentication data</li>
            </ul>
            
            <h3 className="text-xl font-semibold text-gray-800 mb-3">2.2 Usage Data</h3>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>Browser type and version</li>
              <li>IP address and location data</li>
              <li>Pages visited and time spent on pages</li>
              <li>Search queries and preferences</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. How We Use Your Information</h2>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>Process and manage your bookings</li>
              <li>Send booking confirmations and updates</li>
              <li>Personalize your experience</li>
              <li>Improve our services and website</li>
              <li>Send marketing communications (with your consent)</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. Cookies and Tracking Technologies</h2>
            <p className="text-gray-700 mb-4">
              We use cookies and similar tracking technologies to enhance your browsing experience, analyze site traffic, 
              and personalize content. You can control cookie preferences through your browser settings or our cookie consent banner.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. Data Sharing and Disclosure</h2>
            <p className="text-gray-700 mb-4">
              We do not sell your personal information. We may share your information with:
            </p>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>Hotel partners to fulfill bookings</li>
              <li>Payment processors for transaction processing</li>
              <li>Service providers who assist in our operations</li>
              <li>Legal authorities when required by law</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. Your Rights (GDPR)</h2>
            <p className="text-gray-700 mb-4">Under GDPR, you have the right to:</p>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li><strong>Access:</strong> Request a copy of your personal data</li>
              <li><strong>Rectification:</strong> Correct inaccurate or incomplete data</li>
              <li><strong>Erasure:</strong> Request deletion of your personal data</li>
              <li><strong>Portability:</strong> Export your data in a machine-readable format</li>
              <li><strong>Objection:</strong> Object to processing of your data</li>
              <li><strong>Restriction:</strong> Request restriction of processing</li>
            </ul>
            <p className="text-gray-700 mb-4">
              To exercise these rights, please contact us at <a href="mailto:privacy@aerohotels.com" className="text-blue-600 hover:underline">privacy@aerohotels.com</a> 
              or use our data export/deletion endpoints in your account settings.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. Data Security</h2>
            <p className="text-gray-700 mb-4">
              We implement appropriate technical and organizational measures to protect your personal information against 
              unauthorized access, alteration, disclosure, or destruction. This includes encryption, secure servers, 
              and regular security audits.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. Data Retention</h2>
            <p className="text-gray-700 mb-4">
              We retain your personal information only for as long as necessary to fulfill the purposes outlined in this 
              policy, comply with legal obligations, or resolve disputes.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Children's Privacy</h2>
            <p className="text-gray-700 mb-4">
              Our services are not intended for individuals under the age of 18. We do not knowingly collect personal 
              information from children.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">10. Changes to This Policy</h2>
            <p className="text-gray-700 mb-4">
              We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new 
              policy on this page and updating the "Last Updated" date.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">11. Contact Us</h2>
            <p className="text-gray-700 mb-4">
              If you have questions about this Privacy Policy or wish to exercise your rights, please contact us:
            </p>
            <ul className="list-none text-gray-700">
              <li><strong>Email:</strong> <a href="mailto:privacy@aerohotels.com" className="text-blue-600 hover:underline">privacy@aerohotels.com</a></li>
              <li><strong>Address:</strong> Aero Hotels Privacy Team</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}

