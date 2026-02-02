import { useState } from 'react'
import Dialog from './Dialog'

export default function Footer() {
  const [impressumOpen, setImpressumOpen] = useState(false)
  const [datenschutzOpen, setDatenschutzOpen] = useState(false)

  return (
    <>
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center space-x-8 text-sm text-gray-600">
            <button
              onClick={() => setImpressumOpen(true)}
              className="hover:text-gray-900 transition-colors"
            >
              Impressum
            </button>
            <span className="text-gray-300">|</span>
            <button
              onClick={() => setDatenschutzOpen(true)}
              className="hover:text-gray-900 transition-colors"
            >
              Datenschutzerklärung
            </button>
          </div>
          <div className="mt-4 text-center text-xs text-gray-500">
            © {new Date().getFullYear()} Landesamt für Denkmalpflege. Alle Rechte vorbehalten.
          </div>
        </div>
      </footer>

      <Dialog
        isOpen={impressumOpen}
        onClose={() => setImpressumOpen(false)}
        title="Impressum"
      >
        <div className="space-y-4 text-gray-700">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Verantwortlich für den Inhalt:</h3>
            <p>Landesamt für Denkmalpflege</p>
            <p>[Behördenadresse]</p>
            <p>[PLZ Stadt]</p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Kontakt:</h3>
            <p>E-Mail: info@stefanai.de</p>
            <p>Telefon: [Telefonnummer]</p>
          </div>
        </div>
      </Dialog>

      <Dialog
        isOpen={datenschutzOpen}
        onClose={() => setDatenschutzOpen(false)}
        title="Datenschutzerklärung"
      >
        <div className="space-y-4 text-gray-700">
          <p>
            Diese Anwendung verarbeitet hochgeladene Dokumente zur automatischen Kategorisierung und Analyse.
          </p>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Verarbeitete Daten:</h3>
            <ul className="list-disc list-inside space-y-1">
              <li>Hochgeladene Dateien (TAR-Archive, PDFs)</li>
              <li>Extrahierte Textinhalte</li>
              <li>Kategorisierungsergebnisse</li>
            </ul>
          </div>
          <p>
            Die Daten werden ausschließlich zur Verarbeitung verwendet und nach Abschluss der Prüfung gemäß den gesetzlichen Aufbewahrungsfristen behandelt.
          </p>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Bei Fragen zum Datenschutz wenden Sie sich bitte an:</h3>
            <p>info@stefanai.de</p>
          </div>
        </div>
      </Dialog>
    </>
  )
}
