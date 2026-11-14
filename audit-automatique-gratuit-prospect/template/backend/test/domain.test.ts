import { describe, expect, it } from 'vitest';
import { domainFromEmail, domainFromFreeText, extractBookingDomain, normalizeDomain, slugify } from '../src/lib/domain.js';

describe('normalizeDomain', () => {
  it.each([
    ['https://www.Exemple-Renovation.fr/contact?x=1', 'exemple-renovation.fr'],
    ['www.business-x.fr', 'business-x.fr'],
    ['business-x.fr.', 'business-x.fr'],
    ['  http://atelier.business-x.fr/a  ', 'atelier.business-x.fr'],
    ['café-déco.fr', 'xn--caf-dco-dyac.fr'],
  ])('%s -> %s', (input, expected) => expect(normalizeDomain(input)).toBe(expected));

  it.each(['', 'pas un domaine', 'localhost', '127.0.0.1', 'http://10.0.0.1', 'ftp://x.fr', 'contact@x.fr', 'foo', 'x.test', 'internal.local', 'a..fr', 'http://user:pw@x.fr'])(
    'refuse %s',
    (input) => expect(normalizeDomain(input)).toBeNull(),
  );
});

describe('domainFromEmail', () => {
  it('garde un domaine professionnel', () => expect(domainFromEmail('Jean.Dupont@Atelier-Dupont.fr')).toBe('atelier-dupont.fr'));
  it.each(['a@gmail.com', 'a@orange.fr', 'a@outlook.fr', 'a@facebook.com', 'pas-un-email'])('rejette %s', (e) => expect(domainFromEmail(e)).toBeNull());
});

describe('domainFromFreeText', () => {
  it('extrait le domaine d’une phrase', () => expect(domainFromFreeText('Notre site : https://business-marchand.fr/contact (en refonte)')).toBe('business-marchand.fr'));
  it('préfère un domaine pro dans un e-mail', () => expect(domainFromFreeText('contact@business-x.fr')).toBe('business-x.fr'));
  it('ignore les réseaux et les fichiers', () => {
    expect(domainFromFreeText('instagram.com/monentreprise')).toBeNull();
    expect(domainFromFreeText('plan.pdf')).toBeNull();
  });
});

describe('extractBookingDomain', () => {
  const site = (statement: string, answer: string) => ({ statement, answer });
  it('utilise la réponse dont l’intitulé parle de site', () => {
    expect(extractBookingDomain([site('Phone Number', '+33 2 61 91 00 00'), site('Site web de votre entreprise', 'www.atelier-b.fr')], 'jean@gmail.com')).toEqual({ domain: 'atelier-b.fr', via: 'answer' });
  });
  it('reconnaît domaine et url, sans accents ni casse', () => {
    expect(extractBookingDomain([site('Nom de DOMAINE', 'atelier-c.fr')], null).domain).toBe('atelier-c.fr');
    expect(extractBookingDomain([site('URL du site', 'https://atelier-d.com/')], null).domain).toBe('atelier-d.com');
  });
  it('ne se laisse pas prendre par « visite » ou « webinaire » ni par « domaine d’activité »', () => {
    expect(extractBookingDomain([site('Date de visite', 'business-z.fr')], 'a@gmail.com').domain).toBeNull();
    expect(extractBookingDomain([site('Domaine d’activité', 'Rénovation')], 'a@gmail.com').domain).toBeNull();
    expect(extractBookingDomain([site('Comment avez-vous connu notre webinaire ?', 'via x.fr')], 'a@gmail.com').domain).toBeNull();
  });
  it('se replie sur l’e-mail professionnel', () => {
    expect(extractBookingDomain([site('Site web', 'nous n’en avons pas')], 'jean@agence-h.fr')).toEqual({ domain: 'agence-h.fr', via: 'email' });
  });
  it('rend null quand rien n’est exploitable : needs_domain', () => {
    expect(extractBookingDomain([site('Site web', 'instagram.com/x')], 'jean@gmail.com')).toEqual({ domain: null, via: null });
  });
});

describe('slugify', () => {
  it.each([
    ['Exemple Rénovation', 'exemple-renovation'],
    ['Atelier d’Œuvre & Cie', 'atelier-d-oeuvre-cie'],
    ['', 'audit'],
  ])('%s -> %s', (input, expected) => expect(slugify(input)).toBe(expected));
});
