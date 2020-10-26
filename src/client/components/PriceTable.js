import React from 'react';
import { makeStyles } from '@material-ui/core/styles';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';

export default function PriceTable({ tickers }) {
    return (
        <TableContainer component={Paper} className="table-container">
            <Table className="price-table" aria-label="simple table">
                <TableHead>
                    <TableRow>
                        <TableCell className="header-row">Company</TableCell>
                        <TableCell className="header-row" align="right">Unit Price</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    { tickers.map(ticker => {
                            return (
                                <TableRow className="table-row" key={ticker.name}>
                                    <TableCell component="th" scope="row" className="company-name">
                                        {ticker.name.toUpperCase()}
                                    </TableCell>
                                    <TableCell align="right">
                                        ${ticker.price}
                                        { ticker.direction ? <span className="increase">&#9650;</span> : <span className="decrease">&#9660;</span>}
                                    </TableCell>
                                </TableRow>
                            );
                        })
                    }
                </TableBody>
            </Table>
        </TableContainer>
    );
}
