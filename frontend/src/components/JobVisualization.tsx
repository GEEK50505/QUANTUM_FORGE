import React from 'react'
import { ResultsResponse } from '../types'

interface JobVisualizationProps {
    results?: ResultsResponse
}

const JobVisualization: React.FC<JobVisualizationProps> = ({ results }) => {
    if (!results) return null

    const energy = results.energy ?? 0
    const gap = (results.homo_lumo_gap ?? 0) * 27.2114

    return (
        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-900/20 rounded-md">
            <div className="flex items-center justify-between">
                <div>
                    <div className="text-xs text-gray-500">Energy</div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-white">{energy.toFixed(6)} Ha</div>
                </div>
                <div>
                    <div className="text-xs text-gray-500">HOMO-LUMO Gap</div>
                    <div className="text-sm font-semibold text-gray-900 dark:text-white">{gap.toFixed(3)} eV</div>
                </div>
            </div>
        </div>
    )
}

export default JobVisualization
