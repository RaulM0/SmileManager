import { afterEach, expect, test, vi } from "vitest";
import { setAccessToken, setClinicContext } from "../api/client";
import { appointmentsService } from "./appointments";
import { clinicalService } from "./clinical";
import { diagnosticsService } from "./diagnostics";
import { imagesService } from "./images";
import { patientsService } from "./patients";

afterEach(() => {
  setAccessToken(null);
  vi.unstubAllGlobals();
});

test.each([null, "clinic-a"])("clinical services always use clinic endpoints (context: %s)", async (clinic) => {
  setClinicContext(clinic);
  const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(Response.json({})));
  vi.stubGlobal("fetch", fetchMock);
  await patientsService.get("5");
  await appointmentsService.get("7");
  await clinicalService.medicalHistory("5");
  await clinicalService.consent("5");
  await imagesService.get("9");
  await diagnosticsService.list("");
  expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
    "/api/v1/clinics/patients/5/",
    "/api/v1/clinics/appointments/7/",
    "/api/v1/clinics/patients/5/medical-history/",
    "/api/v1/clinics/patients/5/consent/",
    "/api/v1/clinics/clinical-images/9/",
    "/api/v1/clinics/diagnostics/?",
  ]);
  for (const [, options] of fetchMock.mock.calls) {
    expect(new Headers(options.headers).get("X-Clinic-ID")).toBe(clinic);
  }
});
