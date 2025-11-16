import { useEffect } from 'react';

export default function TermsOfServicePage() {
  useEffect(() => {
    document.title = 'Terms of Service - Aero Hotels';
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-sm p-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Terms of Service</h1>
        
        <div className="prose prose-lg max-w-none">
          <p className="text-gray-600 mb-6">
            <strong>Last Updated:</strong> {new Date().toLocaleDateString()}
          </p>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">1. Acceptance of Terms</h2>
            <p className="text-gray-700 mb-4">
              By accessing and using Aero Hotels' website and services, you accept and agree to be bound by these Terms of Service. 
              If you do not agree to these terms, please do not use our services.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">2. Use of Service</h2>
            <h3 className="text-xl font-semibold text-gray-800 mb-3">2.1 Eligibility</h3>
            <p className="text-gray-700 mb-4">
              You must be at least 18 years old to use our services. By using our services, you represent and warrant that 
              you meet this age requirement.
            </p>
            
            <h3 className="text-xl font-semibold text-gray-800 mb-3">2.2 Account Registration</h3>
            <p className="text-gray-700 mb-4">
              You are responsible for maintaining the confidentiality of your account credentials and for all activities that 
              occur under your account.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">3. Bookings and Reservations</h2>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>All bookings are subject to availability and confirmation</li>
              <li>Prices are subject to change until booking is confirmed</li>
              <li>Cancellation and refund policies vary by hotel and booking type</li>
              <li>You are responsible for providing accurate booking information</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">4. Payment Terms</h2>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>Payment is required at the time of booking unless otherwise stated</li>
              <li>We accept major credit cards and other payment methods as displayed</li>
              <li>All prices are in the currency displayed and include applicable taxes</li>
              <li>Refunds are processed according to the cancellation policy</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">5. User Conduct</h2>
            <p className="text-gray-700 mb-4">You agree not to:</p>
            <ul className="list-disc pl-6 text-gray-700 mb-4">
              <li>Use the service for any illegal or unauthorized purpose</li>
              <li>Violate any laws in your jurisdiction</li>
              <li>Transmit any viruses or malicious code</li>
              <li>Attempt to gain unauthorized access to our systems</li>
              <li>Interfere with or disrupt the service</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">6. Intellectual Property</h2>
            <p className="text-gray-700 mb-4">
              All content on our website, including text, graphics, logos, and software, is the property of Aero Hotels or 
              its licensors and is protected by copyright and other intellectual property laws.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">7. Limitation of Liability</h2>
            <p className="text-gray-700 mb-4">
              Aero Hotels acts as an intermediary between you and hotel providers. We are not responsible for the quality, 
              safety, or legality of hotel services. Our liability is limited to the amount you paid for our booking service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">8. Indemnification</h2>
            <p className="text-gray-700 mb-4">
              You agree to indemnify and hold harmless Aero Hotels, its officers, directors, employees, and agents from any 
              claims, damages, losses, or expenses arising from your use of the service or violation of these terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">9. Termination</h2>
            <p className="text-gray-700 mb-4">
              We reserve the right to terminate or suspend your account and access to the service at our sole discretion, 
              without prior notice, for conduct that we believe violates these Terms of Service or is harmful to other users, 
              us, or third parties.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">10. Changes to Terms</h2>
            <p className="text-gray-700 mb-4">
              We reserve the right to modify these Terms of Service at any time. We will notify users of significant changes 
              by posting the updated terms on our website. Your continued use of the service after changes constitutes 
              acceptance of the new terms.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">11. Governing Law</h2>
            <p className="text-gray-700 mb-4">
              These Terms of Service are governed by and construed in accordance with applicable laws. Any disputes arising 
              from these terms will be resolved through binding arbitration or in the appropriate courts.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">12. Contact Information</h2>
            <p className="text-gray-700 mb-4">
              If you have questions about these Terms of Service, please contact us:
            </p>
            <ul className="list-none text-gray-700">
              <li><strong>Email:</strong> <a href="mailto:legal@aerohotels.com" className="text-blue-600 hover:underline">legal@aerohotels.com</a></li>
              <li><strong>Address:</strong> Aero Hotels Legal Department</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}

