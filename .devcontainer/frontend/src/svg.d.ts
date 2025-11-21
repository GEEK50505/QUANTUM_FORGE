/*
Purpose: 
Description: 
Exports: 
Notes: Add a short usage example and expected props/return types.
*/

declare module "*.svg?react" {
  import React = require("react");
  export const ReactComponent: React.FC<React.SVGProps<SVGSVGElement>>;
  const src: string;
  export default src;
}
