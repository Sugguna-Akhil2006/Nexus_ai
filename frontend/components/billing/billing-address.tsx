"use client";

import { useState } from "react";
import { toast } from "sonner";

export interface AddressDetails {
  company: string;
  street: string;
  cityStateZip: string;
  country: string;
}

interface BillingAddressProps {
  initialAddress: AddressDetails;
}

export default function BillingAddress({
  initialAddress,
}: BillingAddressProps) {
  const [address, setAddress] = useState<AddressDetails>(initialAddress);

  const handleEditDetails = () => {
    const company = prompt("Enter Company Name:", address.company);
    if (company === null) return;
    
    const street = prompt("Enter Street Address:", address.street);
    if (street === null) return;
    
    const cityStateZip = prompt("Enter City, State, Zip Code:", address.cityStateZip);
    if (cityStateZip === null) return;
    
    const country = prompt("Enter Country:", address.country);
    if (country === null) return;

    setAddress({
      company: company.trim(),
      street: street.trim(),
      cityStateZip: cityStateZip.trim(),
      country: country.trim(),
    });
    
    toast.success("Billing Address updated successfully!");
  };

  return (
    <div className="bg-surface-container-low border border-outline-variant rounded-xl p-5 shadow-sm flex flex-col justify-between h-full select-none">
      
      {/* Title */}
      <div className="shrink-0 mb-5">
        <h3 className="text-sm md:text-base font-bold text-on-surface uppercase tracking-wider">
          Billing Address
        </h3>
      </div>

      {/* Address Block */}
      <div className="flex-grow select-text space-y-1 text-xs md:text-sm text-on-surface-variant font-medium leading-relaxed">
        <p className="text-on-surface font-extrabold mb-1">
          {address.company}
        </p>
        <p>{address.street}</p>
        <p>{address.cityStateZip}</p>
        <p>{address.country}</p>
        
        {/* Edit details trigger */}
        <div className="pt-4 select-none">
          <button
            onClick={handleEditDetails}
            className="text-on-surface font-bold hover:underline transition-all cursor-pointer bg-transparent border-none p-0 text-xs md:text-sm"
          >
            Edit Details
          </button>
        </div>
      </div>

    </div>
  );
}
