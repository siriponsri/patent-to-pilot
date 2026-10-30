import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { parseLossless } from '../../app/src/core/pyjson.js';

const here = dirname(fileURLToPath(import.meta.url));
export const REPO = resolve(here, '../../../..');
export const read = (rel) => readFileSync(resolve(REPO, rel), 'utf8');

export const FIXTURE_TEXT = read('docs/healthtech/ux/fixtures/ui-fixtures.json');
export const FIXTURES = JSON.parse(FIXTURE_TEXT);
export const SCHEMAS = {
  dossier: JSON.parse(read('schemas/healthtech/DossierVersion.schema.json')),
  manifest: JSON.parse(read('schemas/healthtech/RunManifest.schema.json')),
  event: JSON.parse(read('schemas/healthtech/AcquisitionEvent.schema.json')),
};

/** Lossless copy of one embedded fixture dossier (fresh tree each call). */
export function fixtureDossier(key = 'synthetic_dossier') {
  return parseLossless(FIXTURE_TEXT)[key];
}

/** Apply a mutation to a fresh lossless copy; the original fixture is untouched. */
export function mutated(fn, key = 'synthetic_dossier') {
  const d = fixtureDossier(key);
  fn(d);
  return d;
}
