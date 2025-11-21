/*
Purpose: 
Description: 
Exports: 
Notes: Add a short usage example and expected props/return types.
*/

// Re-export the canonical table components from the `table` folder.
// This file preserves existing import paths that may resolve to this file
// on case-insensitive filesystems. The actual implementation lives in
// `./table/index.tsx`.
import * as TableModule from './table';

// Re-export named components so imports like `../ui/table` resolve correctly
export const Table: any = TableModule.Table;
export const TableHeader: any = TableModule.TableHeader;
export const TableBody: any = TableModule.TableBody;
export const TableRow: any = TableModule.TableRow;
export const TableCell: any = TableModule.TableCell;

// Also provide a default export
export default TableModule.Table;

